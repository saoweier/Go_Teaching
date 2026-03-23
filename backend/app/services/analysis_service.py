import random

from app.domain.enums import MoveKind
from app.domain.models import (
    AnalysisRequest,
    AnalysisResultEnvelope,
    AnalysisSnapshot,
    CandidateMove,
    GameSession,
    Point,
    TeachingNote,
)
from app.engine.katago import KataGoAnalysisEngine, KataGoUnavailableError, gtp_to_point
from app.services.teaching_service import TeachingService


class AnalysisService:
    def __init__(self, engine: KataGoAnalysisEngine, teaching_service: TeachingService):
        self.engine = engine
        self.teaching_service = teaching_service

    def analyze_current(self, game: GameSession, request: AnalysisRequest) -> AnalysisResultEnvelope:
        result = self.engine.analyze(game, max_visits=request.max_visits, include_ownership=request.include_ownership)
        top_moves = [
            CandidateMove(
                move=gtp_to_point(item.move, game.board_size),
                move_gtp=item.move,
                visits=item.visits,
                winrate=item.winrate,
                score_lead=item.score_lead,
                prior=item.prior,
                order=item.order,
                pv=item.pv,
            )
            for item in result.top_moves
        ]
        teaching = self.teaching_service.build_summary(
            game,
            top_moves,
            result.winrate,
            result.score_lead,
            request.ai_profile,
        )
        snapshot = AnalysisSnapshot(
            request_type="current",
            target_move_number=len(game.move_history),
            winrate=result.winrate,
            score_lead=result.score_lead,
            ownership_map=result.ownership if request.include_ownership else [],
            top_moves=top_moves,
        )
        note = TeachingNote(
            request_type="current",
            target_move_number=len(game.move_history),
            summary=teaching,
        )
        game.analysis_snapshots.append(snapshot)
        game.teaching_notes.append(note)
        return AnalysisResultEnvelope(analysis=snapshot, teaching_note=note)

    def analyze_last_move(self, game: GameSession, request: AnalysisRequest) -> AnalysisResultEnvelope:
        envelope = self.analyze_current(game, request)
        envelope.analysis.request_type = "last_move"
        if envelope.teaching_note:
            envelope.teaching_note.request_type = "last_move"
            envelope.teaching_note.summary.key_points.append("建议回看刚才这一步与第一推荐手的后续变化差异。")
        return envelope

    def choose_ai_move(self, game: GameSession, request: AnalysisRequest) -> CandidateMove:
        envelope = self.analyze_current(game, request)
        if not envelope.analysis.top_moves:
            raise KataGoUnavailableError("KataGo did not return any candidate move")
        return self._select_move_by_profile(game, envelope.analysis.top_moves, request.ai_profile)

    def _select_move_by_profile(self, game: GameSession, candidates: list[CandidateMove], profile: str) -> CandidateMove:
        if profile == "serious":
            return candidates[0]
        if profile == "companion":
            return self._select_companion_move(game, candidates)
        return self._sample_close_move(
            candidates=candidates,
            max_candidates=6,
            winrate_gap=0.075,
            score_gap=4.0,
            weights_by_order=[0.34, 0.24, 0.17, 0.11, 0.09, 0.05],
        )

    def _select_companion_move(self, game: GameSession, candidates: list[CandidateMove]) -> CandidateMove:
        best = candidates[0]
        root_pool = self._build_close_pool(
            candidates=candidates,
            max_candidates=8,
            winrate_gap=0.18,
            score_gap=10.0,
        )
        if not root_pool:
            return best

        last_player_move = self._last_play_move_by_color(game, game.user_color)
        move_count = len(game.move_history)

        if last_player_move:
            local_pool = [
                candidate
                for candidate in root_pool
                if candidate.move is not None and self._manhattan_distance(candidate.move, last_player_move) <= 4
            ]
            if local_pool:
                root_pool = local_pool

        weighted_pool: list[tuple[CandidateMove, float]] = []
        for candidate in root_pool:
            weight = self._companion_base_weight(candidate.order, move_count)

            if last_player_move and candidate.move:
                distance = self._manhattan_distance(candidate.move, last_player_move)
                if distance <= 2:
                    weight *= 2.8
                elif distance <= 4:
                    weight *= 1.9
                elif distance <= 6:
                    weight *= 1.15
                else:
                    weight *= 0.55

            if move_count < 20 and candidate.move:
                if self._is_corner_or_side(candidate.move, game.board_size):
                    weight *= 1.35
                else:
                    weight *= 0.85

            if candidate.order == 0 and len(root_pool) > 2:
                weight *= 0.5

            if candidate.order >= 5:
                weight *= 0.75

            weighted_pool.append((candidate, weight))

        if not weighted_pool:
            return best

        choices = [item[0] for item in weighted_pool]
        weights = [item[1] for item in weighted_pool]
        return random.choices(choices, weights=weights, k=1)[0]

    @staticmethod
    def _sample_close_move(
        candidates: list[CandidateMove],
        max_candidates: int,
        winrate_gap: float,
        score_gap: float,
        weights_by_order: list[float],
    ) -> CandidateMove:
        pool = AnalysisService._build_close_pool(candidates, max_candidates, winrate_gap, score_gap)
        if not pool:
            return candidates[0]
        if len(pool) == 1:
            return pool[0]

        weights = [weights_by_order[min(candidate.order, len(weights_by_order) - 1)] for candidate in pool]
        return random.choices(pool, weights=weights, k=1)[0]

    @staticmethod
    def _build_close_pool(
        candidates: list[CandidateMove],
        max_candidates: int,
        winrate_gap: float,
        score_gap: float,
    ) -> list[CandidateMove]:
        best = candidates[0]
        pool: list[CandidateMove] = []

        for candidate in candidates[:max_candidates]:
            if candidate.move is None:
                continue

            within_winrate = (
                best.winrate is None
                or candidate.winrate is None
                or abs(best.winrate - candidate.winrate) <= winrate_gap
            )
            within_score = (
                best.score_lead is None
                or candidate.score_lead is None
                or abs(best.score_lead - candidate.score_lead) <= score_gap
            )

            if within_winrate and within_score:
                pool.append(candidate)

        return pool

    @staticmethod
    def _companion_base_weight(order: int, move_count: int) -> float:
        if move_count < 20:
            table = [0.16, 0.2, 0.2, 0.17, 0.12, 0.08, 0.05, 0.02]
        elif move_count < 80:
            table = [0.12, 0.18, 0.2, 0.18, 0.14, 0.1, 0.05, 0.03]
        else:
            table = [0.1, 0.16, 0.2, 0.18, 0.15, 0.11, 0.07, 0.03]
        return table[min(order, len(table) - 1)]

    @staticmethod
    def _last_play_move_by_color(game: GameSession, color) -> Point | None:
        for move in reversed(game.move_history):
            if move.color == color and move.kind == MoveKind.PLAY and move.point is not None:
                return move.point
        return None

    @staticmethod
    def _manhattan_distance(a: Point, b: Point) -> int:
        return abs(a.row - b.row) + abs(a.col - b.col)

    @staticmethod
    def _is_corner_or_side(point: Point, board_size: int) -> bool:
        edge_band = 4
        near_top = point.row < edge_band
        near_bottom = point.row >= board_size - edge_band
        near_left = point.col < edge_band
        near_right = point.col >= board_size - edge_band
        return near_top or near_bottom or near_left or near_right
