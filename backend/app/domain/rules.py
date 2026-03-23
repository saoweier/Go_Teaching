from __future__ import annotations

from collections import deque

from app.domain.enums import GameStatus, MoveKind, StoneColor
from app.domain.models import BoardState, GameSession, MoveRecord, Point


class IllegalMoveError(ValueError):
    pass


def create_empty_board(size: int, to_play: StoneColor) -> BoardState:
    return BoardState(size=size, grid=[["." for _ in range(size)] for _ in range(size)], to_play=to_play)


def board_hash(grid: list[list[str]], to_play: StoneColor) -> str:
    rows = ["".join(row) for row in grid]
    return f"{to_play.value}:{'/'.join(rows)}"


def neighbors(size: int, row: int, col: int) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < size and 0 <= nc < size:
            coords.append((nr, nc))
    return coords


def collect_group(grid: list[list[str]], row: int, col: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    color = grid[row][col]
    if color == ".":
        return set(), set()
    size = len(grid)
    group: set[tuple[int, int]] = set()
    liberties: set[tuple[int, int]] = set()
    queue = deque([(row, col)])
    while queue:
        cr, cc = queue.popleft()
        if (cr, cc) in group:
            continue
        group.add((cr, cc))
        for nr, nc in neighbors(size, cr, cc):
            value = grid[nr][nc]
            if value == ".":
                liberties.add((nr, nc))
            elif value == color and (nr, nc) not in group:
                queue.append((nr, nc))
    return group, liberties


def point_to_char(color: StoneColor) -> str:
    return "B" if color == StoneColor.BLACK else "W"


def validate_point(board: BoardState, point: Point) -> None:
    if point.row >= board.size or point.col >= board.size:
        raise IllegalMoveError("Move is outside the board")


def apply_play(game: GameSession, color: StoneColor, point: Point) -> MoveRecord:
    board = game.board
    validate_point(board, point)
    if game.status in {GameStatus.FINISHED, GameStatus.RESIGNED}:
        raise IllegalMoveError("Game is already finished")
    if color != board.to_play:
        raise IllegalMoveError("It is not this color's turn")
    if board.grid[point.row][point.col] != ".":
        raise IllegalMoveError("Point is already occupied")
    if board.ko_point and board.ko_point.row == point.row and board.ko_point.col == point.col:
        raise IllegalMoveError("Move violates ko")

    color_char = point_to_char(color)
    enemy_char = point_to_char(color.opposite)
    grid = [row[:] for row in board.grid]
    grid[point.row][point.col] = color_char

    captured: list[tuple[int, int]] = []
    for nr, nc in neighbors(board.size, point.row, point.col):
        if grid[nr][nc] != enemy_char:
            continue
        enemy_group, enemy_liberties = collect_group(grid, nr, nc)
        if not enemy_liberties:
            for gr, gc in enemy_group:
                grid[gr][gc] = "."
            captured.extend(enemy_group)

    own_group, own_liberties = collect_group(grid, point.row, point.col)
    if not own_liberties:
        raise IllegalMoveError("Move is suicidal")

    ko_point = None
    if len(captured) == 1 and len(own_group) == 1 and len(own_liberties) == 1:
        liberty = next(iter(own_liberties))
        ko_point = Point(row=liberty[0], col=liberty[1])

    board.grid = grid
    board.to_play = color.opposite
    board.ko_point = ko_point
    board.captures[color] += len(captured)
    game.status = GameStatus.ACTIVE

    move = MoveRecord(
        move_number=len(game.move_history) + 1,
        color=color,
        kind=MoveKind.PLAY,
        point=point,
        captured_points=[Point(row=r, col=c) for r, c in sorted(captured)],
        board_hash=board_hash(board.grid, board.to_play),
    )
    game.move_history.append(move)
    return move


def apply_pass(game: GameSession, color: StoneColor) -> MoveRecord:
    board = game.board
    if color != board.to_play:
        raise IllegalMoveError("It is not this color's turn")
    previous_status = game.status
    board.to_play = color.opposite
    board.ko_point = None
    game.status = GameStatus.FINISHED if previous_status == GameStatus.PASSED_ONCE else GameStatus.PASSED_ONCE
    move = MoveRecord(
        move_number=len(game.move_history) + 1,
        color=color,
        kind=MoveKind.PASS,
        board_hash=board_hash(board.grid, board.to_play),
    )
    game.move_history.append(move)
    return move


def apply_resign(game: GameSession, color: StoneColor) -> MoveRecord:
    board = game.board
    game.status = GameStatus.RESIGNED
    move = MoveRecord(
        move_number=len(game.move_history) + 1,
        color=color,
        kind=MoveKind.RESIGN,
        board_hash=board_hash(board.grid, board.to_play),
    )
    game.move_history.append(move)
    return move
