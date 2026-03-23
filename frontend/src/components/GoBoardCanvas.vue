<template>
  <div class="board-wrap">
    <div v-if="!session" class="board-empty">
      <p>先创建一局棋，再开始落子、分析和局部聚焦。</p>
    </div>

    <div v-else class="board-panel">
      <div class="board-meta">
        <span class="chip">当前行棋：{{ session.board.to_play }}</span>
        <span class="chip">
          {{ focusMode ? "点击棋盘即可保存 9x9 聚焦区域" : isMyTurn ? "点击空点即可落子" : "当前不是你的回合" }}
        </span>
      </div>

      <div class="board-grid" :style="boardStyle">
        <button
          v-for="cell in cells"
          :key="cell.key"
          class="board-cell"
          :class="cell.className"
          :disabled="!focusMode && !isMyTurn"
          @mouseenter="hoveredKey = cell.key"
          @mouseleave="hoveredKey = null"
          @click="handleCellClick(cell.row, cell.col)"
        >
          <span v-if="cell.starPoint" class="star-point" />
          <span v-if="cell.value !== '.'" class="stone" :class="cell.value === 'B' ? 'black' : 'white'" />
          <span v-if="cell.isLastMove" class="last-move-marker" />
          <span v-else-if="cell.isCandidate" class="candidate-dot" />
          <span
            v-else-if="cell.showHoverPreview"
            class="hover-preview"
            :class="session.board.to_play === 'black' ? 'black' : 'white'"
          />
          <span v-if="cell.isFocusPreview" class="focus-preview" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { CandidateMove, FocusRegion, GameSession, Point } from "@/types/game";

const props = defineProps<{
  session: GameSession | null;
  selectedCandidate: CandidateMove | null;
  focusMode: boolean;
  isMyTurn: boolean;
}>();

const emit = defineEmits<{
  (e: "play-move", point: Point): void;
  (e: "focus-select", region: FocusRegion): void;
}>();

const hoveredKey = ref<string | null>(null);

const starPointSet = new Set([
  "3-3",
  "3-9",
  "3-15",
  "9-3",
  "9-9",
  "9-15",
  "15-3",
  "15-9",
  "15-15",
]);

const lastMove = computed(() => props.session?.move_history.at(-1) ?? null);

const cells = computed(() => {
  const session = props.session;
  if (!session) return [];

  return session.board.grid.flatMap((row, rowIndex) =>
    row.map((value, colIndex) => {
      const key = `${rowIndex}-${colIndex}`;
      const isFocus =
        session.focus_region &&
        rowIndex >= session.focus_region.top &&
        rowIndex < session.focus_region.top + session.focus_region.height &&
        colIndex >= session.focus_region.left &&
        colIndex < session.focus_region.left + session.focus_region.width;
      const isCandidate =
        props.selectedCandidate?.move?.row === rowIndex && props.selectedCandidate?.move?.col === colIndex;
      const isLastMove =
        lastMove.value?.point?.row === rowIndex && lastMove.value?.point?.col === colIndex;
      const showHoverPreview = hoveredKey.value === key && value === "." && !props.focusMode && props.isMyTurn;
      const isFocusPreview = hoveredKey.value === key && props.focusMode && value === ".";

      return {
        key,
        row: rowIndex,
        col: colIndex,
        value,
        starPoint: session.board.size === 19 && starPointSet.has(key),
        isCandidate,
        isLastMove,
        showHoverPreview,
        isFocusPreview,
        className: {
          "is-focus": Boolean(isFocus),
          "is-candidate": isCandidate,
          "is-last-move": isLastMove,
        },
      };
    }),
  );
});

const boardStyle = computed(() => {
  const size = props.session?.board.size ?? 19;
  return {
    gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))`,
  };
});

function handleCellClick(row: number, col: number) {
  if (!props.session) return;
  if (props.focusMode) {
    emit("focus-select", {
      top: Math.max(0, Math.min(row - 4, props.session.board.size - 9)),
      left: Math.max(0, Math.min(col - 4, props.session.board.size - 9)),
      height: 9,
      width: 9,
    });
    return;
  }
  if (!props.isMyTurn) {
    return;
  }
  emit("play-move", { row, col });
}
</script>

<style scoped>
.board-wrap {
  min-height: 680px;
}

.board-empty {
  min-height: 680px;
  display: grid;
  place-items: center;
  border-radius: 28px;
  border: 1px dashed var(--line);
  background: rgba(255, 251, 242, 0.55);
  color: var(--muted);
}

.board-panel {
  padding: 18px;
  border-radius: 28px;
  background:
    linear-gradient(145deg, rgba(255, 245, 219, 0.75), rgba(223, 195, 142, 0.5)),
    linear-gradient(180deg, #e8c58a 0%, #d6ae68 100%);
}

.board-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-bottom: 12px;
}

.board-grid {
  display: grid;
  gap: 1px;
  aspect-ratio: 1;
  width: min(100%, 760px);
  margin: 0 auto;
  padding: 14px;
  border-radius: 24px;
  background: rgba(101, 69, 33, 0.22);
}

.board-cell {
  position: relative;
  aspect-ratio: 1;
  background:
    linear-gradient(90deg, transparent calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% + 0.7px), transparent calc(50% + 0.7px)),
    linear-gradient(0deg, transparent calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% + 0.7px), transparent calc(50% + 0.7px)),
    var(--board-wood);
  border-radius: 2px;
}

.board-cell:hover:not(:disabled) {
  filter: brightness(1.02);
}

.board-cell:disabled {
  cursor: not-allowed;
}

.board-cell.is-focus {
  background:
    linear-gradient(90deg, transparent calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% + 0.7px), transparent calc(50% + 0.7px)),
    linear-gradient(0deg, transparent calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% - 0.7px), rgba(74, 49, 19, 0.42) calc(50% + 0.7px), transparent calc(50% + 0.7px)),
    linear-gradient(180deg, #e5c27f 0%, #dbb56f 100%);
  }

.star-point {
  position: absolute;
  width: 16%;
  height: 16%;
  inset: 42%;
  border-radius: 50%;
  background: rgba(58, 37, 17, 0.82);
}

.stone,
.hover-preview {
  position: absolute;
  inset: 14%;
  border-radius: 50%;
  box-shadow: inset 0 -8px 14px rgba(0, 0, 0, 0.18), 0 5px 12px rgba(0, 0, 0, 0.18);
}

.stone.black,
.hover-preview.black {
  background: radial-gradient(circle at 35% 35%, #676767 0%, #141414 68%);
}

.stone.white,
.hover-preview.white {
  background: radial-gradient(circle at 35% 35%, #ffffff 0%, #d9d7d1 78%);
}

.hover-preview {
  opacity: 0.45;
}

.candidate-dot {
  position: absolute;
  inset: 37%;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 8px rgba(23, 123, 107, 0.12);
}

.last-move-marker {
  position: absolute;
  inset: 40%;
  border-radius: 999px;
  background: #d6593c;
  box-shadow: 0 0 0 5px rgba(214, 89, 60, 0.15);
}

.focus-preview {
  position: absolute;
  inset: 8%;
  border-radius: 10px;
  border: 2px dashed rgba(23, 123, 107, 0.8);
  background: rgba(23, 123, 107, 0.1);
}

@media (max-width: 760px) {
  .board-wrap,
  .board-empty {
    min-height: auto;
  }

  .board-panel {
    padding: 12px;
  }
}
</style>
