from collections import deque

from app.domain.enums import GameStatus, MoveKind, ReviewStatus, StoneColor
from app.domain.models import FinalReview, GameSession, MoveRecord


class ReviewService:
    def build_final_review(self, game: GameSession) -> FinalReview:
        black_territory, white_territory = self._estimate_territory(game)
        black_stones = sum(cell == "B" for row in game.board.grid for cell in row)
        white_stones = sum(cell == "W" for row in game.board.grid for cell in row)

        black_score = black_stones + black_territory + game.board.captures[StoneColor.BLACK]
        white_score = white_stones + white_territory + game.board.captures[StoneColor.WHITE] + game.komi

        estimated_result = self._build_result_label(black_score, white_score)
        key_moments = self._build_key_moments(game)
        local_highlights = self._build_local_highlights(game)
        improvement_points = self._build_improvement_points(game)
        teaching_summary = self._build_teaching_summary(game, estimated_result)

        review = FinalReview(
            status=ReviewStatus.ESTIMATED,
            territory_estimate_black=float(black_score),
            territory_estimate_white=float(white_score),
            capture_count_black=game.board.captures[StoneColor.BLACK],
            capture_count_white=game.board.captures[StoneColor.WHITE],
            estimated_result=estimated_result,
            key_moments=key_moments,
            local_highlights=local_highlights,
            improvement_points=improvement_points,
            teaching_summary=teaching_summary,
            sgf_content=self._build_sgf(game, estimated_result),
        )
        game.final_review = review
        return review

    def _estimate_territory(self, game: GameSession) -> tuple[int, int]:
        grid = game.board.grid
        size = game.board.size
        visited: set[tuple[int, int]] = set()
        black_territory = 0
        white_territory = 0

        for row in range(size):
            for col in range(size):
                if grid[row][col] != "." or (row, col) in visited:
                    continue
                area, borders = self._collect_empty_region(grid, row, col, visited)
                if borders == {"B"}:
                    black_territory += len(area)
                elif borders == {"W"}:
                    white_territory += len(area)

        return black_territory, white_territory

    def _collect_empty_region(
        self,
        grid: list[list[str]],
        row: int,
        col: int,
        visited: set[tuple[int, int]],
    ) -> tuple[set[tuple[int, int]], set[str]]:
        size = len(grid)
        queue = deque([(row, col)])
        area: set[tuple[int, int]] = set()
        borders: set[str] = set()

        while queue:
            cr, cc = queue.popleft()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            area.add((cr, cc))
            for nr, nc in self._neighbors(size, cr, cc):
                value = grid[nr][nc]
                if value == "." and (nr, nc) not in visited:
                    queue.append((nr, nc))
                elif value in {"B", "W"}:
                    borders.add(value)

        return area, borders

    @staticmethod
    def _neighbors(size: int, row: int, col: int) -> list[tuple[int, int]]:
        coords: list[tuple[int, int]] = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size:
                coords.append((nr, nc))
        return coords

    @staticmethod
    def _build_result_label(black_score: float, white_score: float) -> str:
        if black_score > white_score:
            return f"黑方估算领先 {black_score - white_score:.1f} 目"
        if white_score > black_score:
            return f"白方估算领先 {white_score - black_score:.1f} 目"
        return "双方估算接近持平"

    def _build_key_moments(self, game: GameSession) -> list[str]:
        points: list[str] = []
        if game.status == GameStatus.RESIGNED:
            points.append("本局以认输结束，复盘重点应放在认输前 10 手是否还有简化局面的机会。")
        elif game.status == GameStatus.TERMINATED:
            points.append("本局为强制终止，点目结果仅作教学估算，建议重点回看未收完的官子和死活。")
        elif game.status == GameStatus.FINISHED:
            points.append("本局以双方停一手结束，可以优先检查终局前是否还有先手官子遗漏。")

        if game.analysis_snapshots:
            points.append("对局过程中已经有分析快照，可对照候选演化图回看关键转折。")
        if len(game.move_history) >= 12:
            points.append("建议先回看最后 12 手，再回到中盘起势阶段梳理大局方向。")
        return points

    def _build_local_highlights(self, game: GameSession) -> list[str]:
        user_captures = [
            move for move in game.move_history if move.color == game.user_color and move.captured_points and move.point is not None
        ]
        highlights = [
            f"第 {move.move_number} 手在局部提掉 {len(move.captured_points)} 子，说明当时的局部判断是有效的。"
            for move in sorted(user_captures, key=lambda item: len(item.captured_points), reverse=True)[:3]
        ]
        if highlights:
            return highlights

        if game.teaching_notes:
            return [note.summary.headline for note in game.teaching_notes[-2:]]

        return ["这盘棋没有明显的大型吃子片段，更适合从方向感和收束选择上做教学回看。"]

    def _build_improvement_points(self, game: GameSession) -> list[str]:
        ai_captures = [
            move for move in game.move_history if move.color == game.ai_color and move.captured_points and move.point is not None
        ]
        issues = [
            f"第 {move.move_number} 手被对手在局部提掉 {len(move.captured_points)} 子，建议回看这段是否出现了断点或气紧。"
            for move in sorted(ai_captures, key=lambda item: len(item.captured_points), reverse=True)[:3]
        ]

        user_passes = [move for move in game.move_history if move.color == game.user_color and move.kind == MoveKind.PASS]
        if user_passes:
            issues.append("对局中出现过主动停一手，建议确认当时局部是否真的已经走完。")

        if issues:
            return issues[:3]

        return ["这盘棋最大的改进点更可能在大局取舍上，建议结合教学说明判断哪些局部已经可以脱先。"]

    def _build_teaching_summary(self, game: GameSession, estimated_result: str) -> str:
        if game.status == GameStatus.RESIGNED:
            return f"这是认输局的教学复盘。当前估算结果为“{estimated_result}”，但更重要的是回看认输前是否已经明显失衡，以及是否还有更稳的简化手段。"
        if game.status == GameStatus.TERMINATED:
            return f"这是强制终止后的估算点目。当前结果为“{estimated_result}”。教学上建议先判断终止前最后一个战斗区是否已经安定，再决定是继续局部还是转去收大场。"
        return f"这是终局阶段的教学复盘。当前结果为“{estimated_result}”。建议结合棋谱确认哪些地方已经收完，哪些位置仍然存在先手官子。"

    def _build_sgf(self, game: GameSession, estimated_result: str) -> str:
        header = [
            "(;",
            f"GM[1]FF[4]CA[UTF-8]SZ[{game.board_size}]KM[{game.komi}]RU[{game.rules}]",
            f"PB[User]PW[AI]",
        ]
        header.append(f"RE[{estimated_result}]")

        moves = [self._sgf_move(move) for move in game.move_history]
        return "".join(header + moves + [")"])

    def _sgf_move(self, move: MoveRecord) -> str:
        color = "B" if move.color == StoneColor.BLACK else "W"
        if move.kind != MoveKind.PLAY or move.point is None:
            return f";{color}[]"
        return f";{color}[{self._to_sgf_coord(move.point.row)}{self._to_sgf_coord(move.point.col)}]"

    @staticmethod
    def _to_sgf_coord(index: int) -> str:
        return chr(ord("a") + index)
