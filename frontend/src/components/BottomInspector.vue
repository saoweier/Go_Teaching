<template>
  <section class="inspector panel">
    <div class="tab-row">
      <button :class="tabClass('moves')" @click="$emit('change-tab', 'moves')">着手历史</button>
      <button :class="tabClass('analysis')" @click="$emit('change-tab', 'analysis')">分析历史</button>
      <button :class="tabClass('teaching')" @click="$emit('change-tab', 'teaching')">教学说明</button>
      <button :class="tabClass('review')" @click="$emit('change-tab', 'review')">终局总结</button>
      <button :class="tabClass('history')" @click="$emit('change-tab', 'history')">历史对局</button>
    </div>

    <div class="content-area">
      <div v-if="activeTab === 'moves'" class="list-grid">
        <div v-for="move in moveHistory" :key="move.move_number" class="list-card">
          <strong>第 {{ move.move_number }} 手</strong>
          <span>{{ moveLabel(move) }}</span>
        </div>
      </div>

      <div v-else-if="activeTab === 'analysis'" class="list-grid">
        <div v-for="item in analysisHistory" :key="`${item.request_type}-${item.target_move_number}-${item.created_at}`" class="list-card">
          <strong>{{ requestLabel(item.request_type) }}</strong>
          <span>对应手数 {{ item.target_move_number }}</span>
          <span>胜率 {{ item.winrate == null ? "--" : `${(item.winrate * 100).toFixed(1)}%` }}</span>
        </div>
      </div>

      <div v-else-if="activeTab === 'teaching'" class="list-grid">
        <div v-for="note in teachingHistory" :key="`${note.request_type}-${note.target_move_number}-${note.created_at}`" class="list-card">
          <strong>{{ note.summary.headline }}</strong>
          <span>对应手数 {{ note.target_move_number }}</span>
        </div>
      </div>

      <div v-else-if="activeTab === 'history'" class="history-grid">
        <div v-for="item in gameHistory" :key="item.id" class="history-card">
          <div class="history-head">
            <strong>{{ statusLabel(item.status) }}</strong>
            <span>{{ item.move_count }} 手</span>
          </div>
          <p>{{ item.board_size }} 路棋盘 · {{ item.has_review ? "已有复盘" : "未生成复盘" }}</p>
          <p>更新时间 {{ formatDate(item.updated_at) }}</p>
          <div class="history-actions">
            <button class="action-button secondary" type="button" @click="$emit('open-game', item.id)">
              {{ item.status === "suspended" ? "查看挂起局" : "打开对局" }}
            </button>
            <button
              v-if="item.status === 'suspended'"
              class="action-button ghost"
              type="button"
              @click="$emit('resume-game', item.id)"
            >
              继续下
            </button>
          </div>
        </div>
      </div>

      <div v-else class="review-panel">
        <template v-if="finalReview">
          <div class="review-metrics">
            <div class="list-card">
              <strong>黑方估算</strong>
              <span>{{ finalReview.territory_estimate_black.toFixed(1) }}</span>
            </div>
            <div class="list-card">
              <strong>白方估算</strong>
              <span>{{ finalReview.territory_estimate_white.toFixed(1) }}</span>
            </div>
            <div class="list-card">
              <strong>点目结果</strong>
              <span>{{ finalReview.estimated_result }}</span>
            </div>
          </div>

          <p>{{ finalReview.teaching_summary }}</p>

          <div v-if="finalReview.key_moments.length" class="review-points">
            <strong>复盘抓手</strong>
            <ul>
              <li v-for="item in finalReview.key_moments" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div v-if="finalReview.local_highlights.length" class="review-points">
            <strong>局部亮点</strong>
            <ul>
              <li v-for="item in finalReview.local_highlights" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div v-if="finalReview.improvement_points.length" class="review-points">
            <strong>做得不好的地方</strong>
            <ul>
              <li v-for="item in finalReview.improvement_points" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="sgf-panel">
            <strong>棋谱 SGF</strong>
            <textarea :value="finalReview.sgf_content" readonly />
          </div>
        </template>
        <p v-else>还没有终局总结。认输、双停或强制终止后，都可以在这里查看点目和复盘。</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AnalysisSnapshot, FinalReview, GameSummary, MoveRecord, TeachingNote } from "@/types/game";

const props = defineProps<{
  moveHistory: MoveRecord[];
  analysisHistory: AnalysisSnapshot[];
  teachingHistory: TeachingNote[];
  finalReview: FinalReview | null;
  gameHistory: GameSummary[];
  activeTab: "moves" | "analysis" | "teaching" | "review" | "history";
}>();

defineEmits<{
  (e: "change-tab", tab: "moves" | "analysis" | "teaching" | "review" | "history"): void;
  (e: "open-game", gameId: string): void;
  (e: "resume-game", gameId: string): void;
}>();

function tabClass(tab: "moves" | "analysis" | "teaching" | "review" | "history") {
  return ["tab-button", props.activeTab === tab ? "active" : ""];
}

function moveLabel(move: MoveRecord) {
  if (move.kind === "pass") return `${colorLabel(move.color)} 停一手`;
  if (move.kind === "resign") return `${colorLabel(move.color)} 认输`;
  return `${colorLabel(move.color)} 落在 (${move.point?.row}, ${move.point?.col})`;
}

function colorLabel(color: "black" | "white") {
  return color === "black" ? "黑棋" : "白棋";
}

function requestLabel(requestType: "current" | "last_move" | "bot_move") {
  if (requestType === "current") return "当前局面分析";
  if (requestType === "last_move") return "上一手复盘";
  return "AI 应手分析";
}

function statusLabel(status: GameSummary["status"]) {
  if (status === "active") return "进行中";
  if (status === "passed_once") return "一方已停";
  if (status === "suspended") return "已挂起";
  if (status === "finished") return "正常结束";
  if (status === "resigned") return "认输结束";
  return "强制终止";
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}
</script>

<style scoped>
.inspector {
  padding: 18px;
}

.tab-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.tab-button {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--line);
}

.tab-button.active {
  background: var(--accent);
  color: white;
}

.content-area {
  min-height: 220px;
}

.list-grid,
.review-metrics,
.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.list-card,
.history-card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--bg-panel-strong);
  border: 1px solid var(--line);
}

.history-card p,
.list-card span,
.review-panel p,
.review-points li {
  color: var(--muted);
}

.history-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.history-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.review-panel {
  display: grid;
  gap: 14px;
}

.review-points {
  display: grid;
  gap: 8px;
}

.review-points ul {
  margin: 0;
  padding-left: 18px;
}

.sgf-panel {
  display: grid;
  gap: 8px;
}

.sgf-panel textarea {
  min-height: 140px;
  resize: vertical;
  border-radius: 16px;
  border: 1px solid var(--line);
  padding: 12px;
  background: rgba(255, 255, 255, 0.8);
  color: var(--muted);
  font-family: "Cascadia Code", Consolas, monospace;
}
</style>
