import type { BoardState, Point, StoneColor } from "@/types/game";

export interface VariationSnapshot {
  step: number;
  move: string;
  board: string[][];
  moveLabels: Record<string, number>;
}

const GTP_COLUMNS = "ABCDEFGHJKLMNOPQRSTUVWXYZ";

export function buildVariationSnapshots(
  board: BoardState | null,
  pv: string[],
  milestones: number[] = [1, 4, 8, 12],
): VariationSnapshot[] {
  if (!board || pv.length === 0) {
    return [];
  }

  const grid = board.grid.map((row) => [...row]);
  const moveLabels: Record<string, number> = {};
  let toPlay: StoneColor = board.to_play;
  const snapshots: VariationSnapshot[] = [];
  const milestoneSet = new Set(milestones);

  for (let index = 0; index < pv.length; index += 1) {
    const move = pv[index];
    applyMove(grid, moveLabels, board.size, move, toPlay, index + 1);
    const step = index + 1;
    if (milestoneSet.has(step)) {
      snapshots.push({
        step,
        move,
        board: grid.map((row) => [...row]),
        moveLabels: { ...moveLabels },
      });
    }
    toPlay = toPlay === "black" ? "white" : "black";
    if (snapshots.length === milestones.length) {
      break;
    }
  }

  return snapshots;
}

function applyMove(
  grid: string[][],
  moveLabels: Record<string, number>,
  boardSize: number,
  move: string,
  color: StoneColor,
  step: number,
) {
  if (move.toLowerCase() === "pass") {
    return;
  }
  const point = gtpToPoint(move, boardSize);
  if (!point) {
    return;
  }

  const colorChar = color === "black" ? "B" : "W";
  const enemyChar = color === "black" ? "W" : "B";
  grid[point.row][point.col] = colorChar;
  moveLabels[`${point.row}-${point.col}`] = step;

  for (const [nr, nc] of neighbors(boardSize, point.row, point.col)) {
    if (grid[nr][nc] !== enemyChar) {
      continue;
    }
    const enemyGroup = collectGroup(grid, nr, nc);
    if (enemyGroup.liberties.size === 0) {
      for (const [gr, gc] of enemyGroup.stones) {
        grid[gr][gc] = ".";
        delete moveLabels[`${gr}-${gc}`];
      }
    }
  }

  const ownGroup = collectGroup(grid, point.row, point.col);
  if (ownGroup.liberties.size === 0) {
    grid[point.row][point.col] = ".";
    delete moveLabels[`${point.row}-${point.col}`];
  }
}

function gtpToPoint(value: string, boardSize: number): Point | null {
  if (!value || value.toLowerCase() === "pass") {
    return null;
  }
  const col = GTP_COLUMNS.indexOf(value[0].toUpperCase());
  const row = boardSize - Number.parseInt(value.slice(1), 10);
  if (col < 0 || Number.isNaN(row)) {
    return null;
  }
  return { row, col };
}

function neighbors(size: number, row: number, col: number): Array<[number, number]> {
  const result: Array<[number, number]> = [];
  for (const [dr, dc] of [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1],
  ]) {
    const nr = row + dr;
    const nc = col + dc;
    if (nr >= 0 && nr < size && nc >= 0 && nc < size) {
      result.push([nr, nc]);
    }
  }
  return result;
}

function collectGroup(grid: string[][], row: number, col: number) {
  const color = grid[row][col];
  const queue: Array<[number, number]> = [[row, col]];
  const stones = new Set<string>();
  const liberties = new Set<string>();

  while (queue.length > 0) {
    const [cr, cc] = queue.pop()!;
    const key = `${cr},${cc}`;
    if (stones.has(key)) {
      continue;
    }
    stones.add(key);

    for (const [nr, nc] of neighbors(grid.length, cr, cc)) {
      const value = grid[nr][nc];
      if (value === ".") {
        liberties.add(`${nr},${nc}`);
      } else if (value === color && !stones.has(`${nr},${nc}`)) {
        queue.push([nr, nc]);
      }
    }
  }

  return {
    stones: [...stones].map((item) => {
      const [r, c] = item.split(",").map(Number);
      return [r, c] as [number, number];
    }),
    liberties,
  };
}
