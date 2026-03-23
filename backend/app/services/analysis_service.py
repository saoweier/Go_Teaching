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
            return self._select_balanced_move(
                game=game,
                candidates=candidates,
                min_order=3,
                max_order=7,
                target_winrate=self._target_winrate(game, profile),
                allow_teaching_handicap=True,
            )
        return self._select_balanced_move(
            game=game,
            candidates=candidates,
            min_order=2,
            max_order=5,
            target_winrate=self._target_winrate(game, profile),
            allow_teaching_handicap=False,
        )

    def _select_balanced_move(
        self,
        game: GameSession,
        candidates: list[CandidateMove],
        min_order: int,
        max_order: int,
        target_winrate: float,
        allow_teaching_handicap: bool,
    ) -> CandidateMove:
        pool = [candidate for candidate in candidates if candidate.move is not None and min_order <= candidate.order <= max_order]
        if not pool:
            pool = [candidate for candidate in candidates if candidate.move is not None]
        if not pool:
            return candidates[0]

        last_player_move = self._last_play_move_by_color(game, game.user_color)
        if last_player_move:
          local_pool = [
              candidate
              for candidate in pool
              if candidate.move is not None and self._manhattan_distance(candidate.move, last_player_move) <= 5
          ]
          if local_pool:
              pool = local_pool

        weighted_pool: list[tuple[CandidateMove, float]] = []
        for candidate in pool:
            weight = self._target_winrate_weight(self._candidate_ai_winrate(game, candidate), target_winrate)

            if candidate.order < min_order:
                weight *= 0.4
            if candidate.order > max_order:
                weight *= 0.7

            if last_player_move and candidate.move:
                distance = self._manhattan_distance(candidate.move, last_player_move)
                if distance <= 2:
                    weight *= 1.8
                elif distance <= 4:
                    weight *= 1.35
                elif distance >= 8:
                    weight *= 0.6

            if allow_teaching_handicap and self._looks_like_hard_punish(candidates):
                if candidate.order == 0:
                    weight *= 0.08
                elif candidate.order == 1:
                    weight *= 0.45

            weighted_pool.append((candidate, weight))

        if not weighted_pool:
            return candidates[0]

        choices = [item[0] for item in weighted_pool]
        weights = [item[1] for item in weighted_pool]
        return random.choices(choices, weights=weights, k=1)[0]

    @staticmethod
    def _target_winrate(game: GameSession, profile: str) -> float:
        move_count = len(game.move_history)
        if profile == "companion":
            if move_count < 20:
                return 0.52
            if move_count < 50:
                return 0.55
            return 0.56
        if move_count < 20:
            return 0.55
        if move_count < 50:
            return 0.58
        return 0.6

    @staticmethod
    def _target_winrate_weight(candidate_winrate: float | None, target_winrate: float) -> float:
        if candidate_winrate is None:
            return 1.0
        distance = abs(candidate_winrate - target_winrate)
        if distance <= 0.015:
            return 2.5
        if distance <= 0.03:
            return 2.0
        if distance <= 0.05:
            return 1.55
        if distance <= 0.08:
            return 1.1
        return 0.6

    @staticmethod
    def _candidate_ai_winrate(game: GameSession, candidate: CandidateMove) -> float | None:
        if candidate.winrate is None:
            return None
        if game.ai_color.value == "black":
            return candidate.winrate
        return 1 - candidate.winrate

    @staticmethod
    def _looks_like_hard_punish(candidates: list[CandidateMove]) -> bool:
        if len(candidates) < 2:
            return False
        best = candidates[0]
        second = candidates[1]
        if best.winrate is not None and second.winrate is not None and abs(best.winrate - second.winrate) >= 0.05:
            return True
        if best.score_lead is not None and second.score_lead is not None and abs(best.score_lead - second.score_lead) >= 3.0:
            return True
        return False

    @staticmethod
    def _last_play_move_by_color(game: GameSession, color) -> Point | None:
        for move in reversed(game.move_history):
            if move.color == color and move.kind == MoveKind.PLAY and move.point is not None:
                return move.point
        return None

    @staticmethod
    def _manhattan_distance(a: Point, b: Point) -> int:
        return abs(a.row - b.row) + abs(a.col - b.col)
