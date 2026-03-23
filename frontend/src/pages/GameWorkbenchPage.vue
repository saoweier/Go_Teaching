<template>
  <div class="shell">
    <div class="workbench">
      <div class="workspace-grid">
        <div class="board-column">
          <BoardControlBar
            :ai-profile="store.aiProfile"
            :can-play-ai="store.canPlayAiMove"
            :creating-game="store.isCreatingGame"
            :playing-ai="store.isPlayingAiMove"
            :focus-mode="focusMode"
            :session="store.gameSession"
            @change-ai-profile="store.setAiProfile"
            @new-game="handleNewGame"
            @ai-move="handleAiMove"
            @pass="store.submitPass"
            @toggle-focus="toggleFocusMode"
          />

          <BoardWorkspace
            :session="store.gameSession"
            :selected-candidate="selectedCandidate"
            :focus-mode="focusMode"
            :analysis-stale="store.isAnalysisStale"
            :is-my-turn="Boolean(store.isMyTurn)"
            :is-waiting-ai="store.isPlayingAiMove"
            @play-move="handleUserMove"
            @focus-select="handleFocusSelect"
          />
        </div>

        <AnalysisSidebar
          :analysis="store.currentAnalysis"
          :board="store.gameSession?.board ?? null"
          :teaching-note="store.currentTeachingNote"
          :analysis-stale="store.isAnalysisStale"
          :selected-candidate-index="selectedCandidateIndex"
          :can-analyze="store.canAnalyze"
          :analyzing="store.isAnalyzing"
          :reviewing="store.isGeneratingFinalReview"
          :auto-analyze-enabled="store.autoAnalyzeEnabled"
          @select-candidate="selectedCandidateIndex = $event"
          @analyze-current="handleAnalyzeCurrent"
          @analyze-last-move="handleAnalyzeLastMove"
          @toggle-auto-analyze="store.toggleAutoAnalyze"
          @final-review="handleFinalReview"
          @resign="handleResign"
        />
      </div>

      <BottomInspector
        :move-history="store.gameSession?.move_history ?? []"
        :analysis-history="store.analysisHistory"
        :teaching-history="store.teachingHistory"
        :final-review="store.finalReview"
        :active-tab="bottomTab"
        @change-tab="bottomTab = $event"
      />

      <div v-if="store.lastError" class="error-banner panel">
        {{ store.lastError }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AnalysisSidebar from "@/components/AnalysisSidebar.vue";
import BoardControlBar from "@/components/BoardControlBar.vue";
import BoardWorkspace from "@/components/BoardWorkspace.vue";
import BottomInspector from "@/components/BottomInspector.vue";
import { useGameSessionStore } from "@/stores/gameSession";
import type { FocusRegion } from "@/types/game";

const store = useGameSessionStore();
const bottomTab = ref<"moves" | "analysis" | "teaching" | "review">("moves");
const focusMode = ref(false);
const selectedCandidateIndex = ref(0);

const selectedCandidate = computed(() => store.currentAnalysis?.top_moves[selectedCandidateIndex.value] ?? null);

async function handleNewGame() {
  const shouldCreate = window.confirm("确定开始新对局吗？当前对局进度会被保留在历史里，但界面会切换到新棋局。");
  if (!shouldCreate) return;

  selectedCandidateIndex.value = 0;
  bottomTab.value = "moves";
  focusMode.value = false;
  await store.createNewGame("black");
}

async function handleAnalyzeCurrent() {
  selectedCandidateIndex.value = 0;
  bottomTab.value = "analysis";
  await store.requestCurrentAnalysis();
}

async function handleUserMove(point: { row: number; col: number }) {
  selectedCandidateIndex.value = 0;
  bottomTab.value = store.autoAnalyzeEnabled ? "analysis" : "moves";
  await store.submitMoveThenAi(point);
}

async function handleAiMove() {
  selectedCandidateIndex.value = 0;
  bottomTab.value = store.autoAnalyzeEnabled ? "analysis" : "moves";
  await store.playAiTurnAndAnalyze();
}

async function handleAnalyzeLastMove() {
  selectedCandidateIndex.value = 0;
  bottomTab.value = "teaching";
  await store.requestLastMoveAnalysis();
}

async function handleFinalReview() {
  bottomTab.value = "review";
  await store.generateFinalReview();
}

async function handleResign() {
  const shouldResign = window.confirm("确定认输吗？认输后会自动生成总结和复盘。");
  if (!shouldResign) return;

  bottomTab.value = "review";
  await store.submitResignAndReview();
}

function toggleFocusMode() {
  focusMode.value = !focusMode.value;
}

async function handleFocusSelect(region: FocusRegion) {
  await store.updateFocusRegion(region);
  focusMode.value = false;
}

onMounted(async () => {
  const persistedGameId = store.getPersistedGameId();
  if (persistedGameId) {
    try {
      await store.restoreGame(persistedGameId);
    } catch {
      // Ignore restore failures and let the user start a fresh game.
    }
  }
});
</script>

<style scoped>
.workbench {
  display: grid;
  gap: 18px;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(360px, 0.92fr);
  gap: 18px;
  align-items: start;
}

.board-column {
  display: grid;
  gap: 16px;
  align-content: start;
}

.error-banner {
  padding: 14px 18px;
  border-color: rgba(157, 75, 56, 0.25);
  color: var(--danger);
}

@media (max-width: 1120px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }
}
</style>
