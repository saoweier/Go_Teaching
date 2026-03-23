<template>
  <aside class="sidebar panel">
    <section class="sidebar-card analysis-actions">
      <div class="action-head">
        <div>
          <p class="section-title">教学分析</p>
          <h3>局面概览与讲解</h3>
        </div>
        <label class="toggle-row">
          <input :checked="autoAnalyzeEnabled" type="checkbox" @change="$emit('toggle-auto-analyze')" />
          <span>自动分析</span>
        </label>
      </div>

      <div class="action-buttons">
        <button class="action-button secondary" :disabled="!canAnalyze || analyzing" @click="$emit('analyze-current')">
          {{ analyzing ? "分析中..." : "分析当前局面" }}
        </button>
        <button class="action-button secondary" :disabled="!canAnalyze || analyzing" @click="$emit('analyze-last-move')">
          分析上一手
        </button>
        <button class="action-button ghost" :disabled="!canAnalyze || reviewing" @click="$emit('final-review')">
          {{ reviewing ? "生成中..." : "终局复盘" }}
        </button>
      </div>
    </section>

    <section class="sidebar-card">
      <p class="section-title">局面概览</p>
      <div class="metric-row">
        <div class="metric-box">
          <span>胜率</span>
          <strong>{{ formatPercent(analysis?.winrate) }}</strong>
        </div>
        <div class="metric-box">
          <span>目差</span>
          <strong>{{ formatScore(analysis?.score_lead) }}</strong>
        </div>
      </div>
      <p class="stale-note">{{ analysisStale ? "当前展示的分析已过期" : "当前展示的分析与局面同步" }}</p>
    </section>

    <section class="sidebar-card">
      <div class="summary-head">
        <p class="section-title">教学说明</p>
        <span v-if="teachingNote" class="profile-pill">{{ profileLabel(teachingNote.summary.profile) }}</span>
      </div>
      <h3>{{ teachingNote?.summary.headline ?? "还没有教学说明" }}</h3>
      <p v-if="teachingNote?.summary.why_this_move" class="explain-block">
        <strong>为什么这么下：</strong>{{ teachingNote.summary.why_this_move }}
      </p>
      <p v-if="teachingNote?.summary.impact_summary" class="explain-block">
        <strong>怎么影响后势：</strong>{{ teachingNote.summary.impact_summary }}
      </p>
      <ul>
        <li v-for="item in teachingNote?.summary.key_points ?? []" :key="item">{{ item }}</li>
      </ul>
    </section>

    <section class="sidebar-card">
      <div class="variation-head">
        <p class="section-title">候选演化</p>
        <span class="variation-note">切换候选点，点击快照可放大查看。</span>
      </div>

      <div class="candidate-tabs">
        <button
          v-for="(move, index) in analysis?.top_moves ?? []"
          :key="`${move.move_gtp}-${index}`"
          class="candidate-tab"
          :class="{ selected: selectedCandidateIndex === index }"
          @click="$emit('select-candidate', index)"
        >
          <strong>{{ move.move_gtp }}</strong>
          <span>{{ formatPercent(move.winrate) }}</span>
        </button>
      </div>

      <template v-if="selectedCandidate">
        <div class="candidate-summary">
          <div class="summary-chip">候选点 {{ selectedCandidate.move_gtp }}</div>
          <div class="summary-chip">访问 {{ selectedCandidate.visits }}</div>
          <div class="summary-chip">目差 {{ formatScore(selectedCandidate.score_lead) }}</div>
        </div>

        <div v-if="variationSnapshots.length" class="snapshot-grid">
          <button
            v-for="snapshot in variationSnapshots"
            :key="`${selectedCandidate.move_gtp}-${snapshot.step}`"
            class="snapshot-card"
            type="button"
            @click="activeSnapshot = snapshot"
          >
            <div class="snapshot-meta">
              <strong>第 {{ snapshot.step }} 手后</strong>
              <span>落在 {{ snapshot.move }}</span>
            </div>
            <VariationPreviewBoard :board="snapshot.board" :move-labels="snapshot.moveLabels" :size="boardSize" />
          </button>
        </div>

        <p class="empty-note">演化图会优先展示 1、4、8、12 手后的局面快照，方便看走势而不是硬读坐标。</p>
      </template>

      <p v-else class="empty-note">先完成一次分析，才能展开候选点的后续演化。</p>
    </section>

    <div class="danger-row">
      <button class="danger-button" :disabled="!canAnalyze" @click="$emit('resign')">认输并复盘</button>
    </div>

    <div v-if="activeSnapshot" class="snapshot-modal" @click.self="activeSnapshot = null">
      <div class="snapshot-modal-card">
        <div class="modal-head">
          <div>
            <strong>第 {{ activeSnapshot.step }} 手后</strong>
            <p>落在 {{ activeSnapshot.move }}</p>
          </div>
          <button class="close-button" type="button" @click="activeSnapshot = null">关闭</button>
        </div>
        <VariationPreviewBoard :board="activeSnapshot.board" :move-labels="activeSnapshot.moveLabels" :size="boardSize" large />
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import VariationPreviewBoard from "@/components/VariationPreviewBoard.vue";
import type { AiProfile, AnalysisSnapshot, BoardState, CandidateMove, TeachingNote } from "@/types/game";
import { buildVariationSnapshots, type VariationSnapshot } from "@/utils/variationPreview";

const props = defineProps<{
  analysis: AnalysisSnapshot | null;
  teachingNote: TeachingNote | null;
  analysisStale: boolean;
  selectedCandidateIndex: number;
  canAnalyze: boolean;
  analyzing: boolean;
  reviewing: boolean;
  autoAnalyzeEnabled: boolean;
  board: BoardState | null;
}>();

defineEmits<{
  (e: "select-candidate", index: number): void;
  (e: "analyze-current"): void;
  (e: "analyze-last-move"): void;
  (e: "toggle-auto-analyze"): void;
  (e: "final-review"): void;
  (e: "resign"): void;
}>();

const selectedCandidate = computed<CandidateMove | null>(() => props.analysis?.top_moves[props.selectedCandidateIndex] ?? null);
const boardSize = computed(() => props.board?.size ?? 19);
const variationSnapshots = computed(() => buildVariationSnapshots(props.board, selectedCandidate.value?.pv ?? []));
const activeSnapshot = ref<VariationSnapshot | null>(null);

function formatPercent(value: number | null | undefined) {
  if (value == null) return "--";
  return `${(value * 100).toFixed(1)}%`;
}

function formatScore(value: number | null | undefined) {
  if (value == null) return "--";
  return value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
}

function profileLabel(profile: AiProfile) {
  if (profile === "companion") return "陪练讲法";
  if (profile === "serious") return "认真讲法";
  return "教学讲法";
}
</script>

<style scoped>
.sidebar {
  padding: 18px;
  display: grid;
  gap: 14px;
}

.sidebar-card {
  padding: 18px;
  border-radius: 20px;
  background: var(--bg-panel-strong);
  border: 1px solid var(--line);
}

.analysis-actions {
  display: grid;
  gap: 16px;
}

.action-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.action-head h3 {
  margin: 6px 0 0;
  font-size: 22px;
}

.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(23, 123, 107, 0.08);
  color: var(--muted);
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-head,
.variation-head,
.modal-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.profile-pill,
.summary-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
}

.variation-note,
.stale-note,
.empty-note,
.snapshot-meta span,
.modal-head p {
  color: var(--muted);
}

.sidebar-card h3 {
  margin: 10px 0 12px;
  font-size: 24px;
  line-height: 1.25;
}

.sidebar-card ul {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
}

.explain-block {
  margin: 0 0 12px;
  line-height: 1.6;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 12px;
}

.metric-box {
  padding: 14px;
  border-radius: 16px;
  background: rgba(23, 123, 107, 0.08);
}

.metric-box span {
  color: var(--muted);
}

.metric-box strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
}

.candidate-tabs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
  gap: 10px;
  margin: 12px 0;
}

.candidate-tab,
.snapshot-card {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: 14px;
  background: white;
  border: 1px solid var(--line);
  text-align: left;
}

.candidate-tab.selected {
  border-color: rgba(23, 123, 107, 0.35);
  background: var(--accent-soft);
}

.candidate-tab span {
  color: var(--muted);
}

.candidate-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(172px, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.snapshot-meta {
  display: grid;
  gap: 2px;
}

.danger-row {
  display: flex;
  justify-content: flex-end;
}

.danger-button {
  padding: 12px 16px;
  border-radius: 999px;
  background: rgba(157, 75, 56, 0.12);
  color: var(--danger);
  border: 1px solid rgba(157, 75, 56, 0.2);
  font-weight: 700;
}

.snapshot-modal {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(20, 18, 15, 0.48);
  z-index: 50;
}

.snapshot-modal-card {
  display: grid;
  gap: 16px;
  padding: 20px;
  width: min(80vw, 620px);
  border-radius: 24px;
  background: rgba(255, 251, 242, 0.98);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

.close-button {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--line);
}

@media (max-width: 900px) {
  .action-head,
  .summary-head,
  .variation-head,
  .modal-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
