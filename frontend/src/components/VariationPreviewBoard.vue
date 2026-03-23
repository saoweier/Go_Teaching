<template>
  <div class="mini-board" :class="{ large: props.large }" :style="{ gridTemplateColumns: `repeat(${props.size}, minmax(0, 1fr))` }">
    <div v-for="cell in cells" :key="cell.key" class="mini-cell">
      <span v-if="cell.starPoint" class="star-point" />
      <span v-if="cell.value !== '.'" class="stone" :class="cell.value === 'B' ? 'black' : 'white'">
        <span v-if="cell.moveLabel" class="move-label" :class="{ compact: cell.moveLabel >= 10 }">
          {{ cell.moveLabel }}
        </span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  board: string[][];
  moveLabels?: Record<string, number>;
  size: number;
  large?: boolean;
}>();

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

const cells = computed(() =>
  props.board.flatMap((row, rowIndex) =>
    row.map((value, colIndex) => ({
      key: `${rowIndex}-${colIndex}`,
      value,
      moveLabel: props.moveLabels?.[`${rowIndex}-${colIndex}`],
      starPoint: props.size === 19 && starPointSet.has(`${rowIndex}-${colIndex}`),
    })),
  ),
);
</script>

<style scoped>
.mini-board {
  display: grid;
  gap: 1px;
  aspect-ratio: 1;
  width: 100%;
  max-width: 168px;
  padding: 6px;
  border-radius: 14px;
  background: rgba(101, 69, 33, 0.22);
}

.mini-board.large {
  max-width: min(72vw, 520px);
  padding: 12px;
  border-radius: 18px;
}

.mini-cell {
  position: relative;
  aspect-ratio: 1;
  background:
    linear-gradient(90deg, transparent calc(50% - 0.5px), rgba(74, 49, 19, 0.38) calc(50% - 0.5px), rgba(74, 49, 19, 0.38) calc(50% + 0.5px), transparent calc(50% + 0.5px)),
    linear-gradient(0deg, transparent calc(50% - 0.5px), rgba(74, 49, 19, 0.38) calc(50% - 0.5px), rgba(74, 49, 19, 0.38) calc(50% + 0.5px), transparent calc(50% + 0.5px)),
    var(--board-wood);
}

.star-point {
  position: absolute;
  width: 16%;
  height: 16%;
  inset: 42%;
  border-radius: 50%;
  background: rgba(58, 37, 17, 0.82);
}

.stone {
  position: absolute;
  inset: 18%;
  border-radius: 50%;
  display: grid;
  place-items: center;
  box-shadow: inset 0 -4px 8px rgba(0, 0, 0, 0.16), 0 2px 6px rgba(0, 0, 0, 0.14);
}

.stone.black {
  background: radial-gradient(circle at 35% 35%, #676767 0%, #141414 68%);
}

.stone.white {
  background: radial-gradient(circle at 35% 35%, #ffffff 0%, #d9d7d1 78%);
}

.move-label {
  font-size: 8px;
  font-weight: 700;
  line-height: 1;
  color: #f7f7f7;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.35);
}

.stone.white .move-label {
  color: #1f1b15;
  text-shadow: none;
}

.move-label.compact {
  font-size: 6px;
}

.mini-board.large .move-label {
  font-size: 14px;
}

.mini-board.large .move-label.compact {
  font-size: 11px;
}
</style>
