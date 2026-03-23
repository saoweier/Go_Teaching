<template>
  <section class="inspector panel">
    <div class="tab-row">
      <button :class="tabClass('moves')" @click="$emit('change-tab', 'moves')">着手历史</button>
      <button :class="tabClass('analysis')" @click="$emit('change-tab', 'analysis')">分析历史</button>
      <button :class="tabClass('teaching')" @click="$emit('change-tab', 'teaching')">教学说明</button>
      <button :class="tabClass('review')" @click="$emit('change-tab', 'review')">终局总结</button>
    </div>

    <div class="content-area">
      <div v-if="activeTab === 'moves'" class="list-grid">
        <div v-for="move in moveHistory" :key="move.move_number" class="list-card">
          <strong>{{ move.move_number }}. {{ move.color }} {{ move.kind }}</strong>
          <span>{{ move.point ? `${move.point.row}, ${move.point.col}` : "pass/resign" }}</span>
        </div>
      </div>

      <div v-else-if="activeTab === 'analysis'" class="list-grid">
        <div v-for="item in analysisHistory" :key="`${item.request_type}-${item.target_move_number}-${item.created_at}`" class="list-card">
          <strong>{{ item.request_type }} / 手数 {{ item.target_move_number }}</strong>
          <span>胜率 {{ item.winrate == null ? "--" : `${(item.winrate * 100).toFixed(1)}%` }}</span>
        </div>
      </div>

      <div v-else-if="activeTab === 'teaching'" class="list-grid">
        <div v-for="note in teachingHistory" :key="`${note.request_type}-${note.target_move_number}-${note.created_at}`" class="list-card">
          <strong>{{ note.summary.headline }}</strong>
          <span>对应手数 {{ note.target_move_number }}</span>
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
          </div>
          <p>{{ finalReview.teaching_summary }}</p>
          <div v-if="finalReview.key_moments.length" class="review-points">
            <strong>复盘抓手</strong>
            <ul>
              <li v-for="item in finalReview.key_moments" :key="item">{{ item }}</li>
            </ul>
          </div>
        </template>
        <p v-else>还没有终局总结，点击顶部“终局复盘”生成。</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AnalysisSnapshot, FinalReview, MoveRecord, TeachingNote } from "@/types/game";

const props = defineProps<{
  moveHistory: MoveRecord[];
  analysisHistory: AnalysisSnapshot[];
  teachingHistory: TeachingNote[];
  finalReview: FinalReview | null;
  activeTab: "moves" | "analysis" | "teaching" | "review";
}>();

defineEmits<{
  (e: "change-tab", tab: "moves" | "analysis" | "teaching" | "review"): void;
}>();

function tabClass(tab: "moves" | "analysis" | "teaching" | "review") {
  return ["tab-button", props.activeTab === tab ? "active" : ""];
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
  min-height: 190px;
}

.list-grid,
.review-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.list-card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--bg-panel-strong);
  border: 1px solid var(--line);
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

.list-card span,
.review-panel p,
.review-points li {
  color: var(--muted);
}
</style>
