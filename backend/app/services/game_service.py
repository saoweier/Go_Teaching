from datetime import datetime, timezone

from app.domain.enums import GameStatus, MoveKind, StoneColor
from app.domain.models import CreateGameRequest, FocusRegion, FocusRegionRequest, GameSession, GameSummary, MoveRequest
from app.domain.rules import IllegalMoveError, apply_pass, apply_play, apply_resign, create_empty_board
from app.stores.game_store import InMemoryGameStore


class GameNotFoundError(KeyError):
    pass


class GameService:
    def __init__(self, store: InMemoryGameStore):
        self.store = store

    def create_game(self, request: CreateGameRequest) -> GameSession:
        board = create_empty_board(request.board_size, StoneColor.BLACK)
        game = GameSession(
            board_size=request.board_size,
            user_color=request.user_color,
            ai_color=request.user_color.opposite,
            komi=request.komi,
            rules=request.rules,
            board=board,
        )
        return self.store.save(game)

    def get_game(self, game_id: str) -> GameSession:
        game = self.store.get(game_id)
        if game is None:
            raise GameNotFoundError(game_id)
        return game

    def list_games(self) -> list[GameSummary]:
        return [
            GameSummary(
                id=game.id,
                board_size=game.board_size,
                user_color=game.user_color,
                ai_color=game.ai_color,
                status=game.status,
                move_count=len(game.move_history),
                end_reason=game.end_reason,
                created_at=game.created_at,
                updated_at=game.updated_at,
                ended_at=game.ended_at,
                has_review=game.final_review is not None,
            )
            for game in self.store.list_all()
        ]

    def apply_move(self, game_id: str, request: MoveRequest, color: StoneColor) -> GameSession:
        game = self.get_game(game_id)
        if request.kind == MoveKind.PLAY:
            if request.point is None:
                raise IllegalMoveError("Point is required for play")
            apply_play(game, color, request.point)
        elif request.kind == MoveKind.PASS:
            apply_pass(game, color)
        elif request.kind == MoveKind.RESIGN:
            apply_resign(game, color)
        if game.status == GameStatus.FINISHED:
            game.end_reason = "two_passes"
            game.ended_at = datetime.now(timezone.utc)
        elif game.status == GameStatus.RESIGNED:
            game.end_reason = "resigned"
            game.ended_at = datetime.now(timezone.utc)
        game.updated_at = datetime.now(timezone.utc)
        return self.store.save(game)

    def set_focus_region(self, game_id: str, request: FocusRegionRequest) -> GameSession:
        game = self.get_game(game_id)
        if request.top + request.height > game.board_size or request.left + request.width > game.board_size:
            raise ValueError("Focus region exceeds board size")
        game.focus_region = FocusRegion(**request.model_dump())
        game.updated_at = datetime.now(timezone.utc)
        return self.store.save(game)

    def suspend_game(self, game_id: str) -> GameSession:
        game = self.get_game(game_id)
        if game.status in {GameStatus.FINISHED, GameStatus.RESIGNED, GameStatus.TERMINATED}:
            raise IllegalMoveError("Finished games cannot be suspended")
        game.status = GameStatus.SUSPENDED
        game.updated_at = datetime.now(timezone.utc)
        return self.store.save(game)

    def resume_game(self, game_id: str) -> GameSession:
        game = self.get_game(game_id)
        if game.status != GameStatus.SUSPENDED:
            raise IllegalMoveError("Only suspended games can be resumed")
        game.status = GameStatus.ACTIVE
        game.updated_at = datetime.now(timezone.utc)
        return self.store.save(game)

    def terminate_game(self, game_id: str) -> GameSession:
        game = self.get_game(game_id)
        if game.status in {GameStatus.FINISHED, GameStatus.RESIGNED, GameStatus.TERMINATED}:
            raise IllegalMoveError("Game is already finished")
        game.status = GameStatus.TERMINATED
        game.end_reason = "terminated"
        game.ended_at = datetime.now(timezone.utc)
        game.updated_at = game.ended_at
        return self.store.save(game)
