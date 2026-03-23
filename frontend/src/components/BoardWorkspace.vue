<template>
  <section class="board-shell panel">
    <div class="board-header">
      <div>
        <p class="section-title">棋盘工作区</p>
        <h2>{{ focusMode ? "局部聚焦选择中" : "主棋盘" }}</h2>
      </div>
      <div class="board-flags">
        <span class="chip">{{ isMyTurn ? "轮到你落子" : "等待 AI 或对局状态变化" }}</span>
        <span class="chip">{{ session?.focus_region ? "已保存聚焦区域" : "全盘视图" }}</span>
        <span class="chip">{{ analysisStale ? "分析已过期" : "分析同步" }}</span>
      </div>
    </div>

    <div class="board-stage">
      <GoBoardCanvas
        :session="session"
        :selected-candidate="selectedCandidate"
        :focus-mode="focusMode"
        :is-my-turn="isMyTurn"
        @play-move="$emit('play-move', $event)"
        @focus-select="$emit('focus-select', $event)"
      />

      <div v-if="isWaitingAi" class="waiting-overlay">
        <div class="waiting-card">
          <div class="thinking-dots">
            <span />
            <span />
            <span />
          </div>
          <strong>AI 正在应手</strong>
          <p>请稍等，系统正在推进下一步。</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import GoBoardCanvas from "@/components/GoBoardCanvas.vue";
import type { CandidateMove, FocusRegion, GameSession, Point } from "@/types/game";

defineProps<{
  session: GameSession | null;
  selectedCandidate: CandidateMove | null;
  focusMode: boolean;
  analysisStale: boolean;
  isMyTurn: boolean;
  isWaitingAi: boolean;
}>();

defineEmits<{
  (e: "play-move", point: Point): void;
  (e: "focus-select", region: FocusRegion): void;
}>();
</script>

<style scoped>
.board-shell {
  padding: 18px;
}

.board-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.board-header h2 {
  margin: 6px 0 0;
  font-size: 28px;
}

.board-flags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.board-stage {
  position: relative;
}

.waiting-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  border-radius: 28px;
  background: rgba(248, 241, 226, 0.68);
  backdrop-filter: blur(4px);
}

.waiting-card {
  display: grid;
  justify-items: center;
  gap: 10px;
  padding: 22px 26px;
  border-radius: 22px;
  background: rgba(255, 251, 242, 0.96);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

.waiting-card p {
  margin: 0;
  color: var(--muted);
}

.thinking-dots {
  display: flex;
  gap: 8px;
}

.thinking-dots span {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--accent);
  animation: thinking-bounce 1.1s infinite ease-in-out;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes thinking-bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.35;
  }
  40% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

@media (max-width: 760px) {
  .board-header {
    flex-direction: column;
  }

  .board-flags {
    justify-content: flex-start;
  }
}
</style>
