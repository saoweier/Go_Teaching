from datetime import datetime, timezone

from app.domain.enums import MoveKind, StoneColor
from app.domain.models import CreateGameRequest, FocusRegion, FocusRegionRequest, GameSession, MoveRequest
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
        game.updated_at = datetime.now(timezone.utc)
        return self.store.save(game)

    def set_focus_region(self, game_id: str, request: FocusRegionRequest) -> GameSession:
        game = self.get_game(game_id)
        if request.top + request.height > game.board_size or request.left + request.width > game.board_size:
            raise ValueError("Focus region exceeds board size")
        game.focus_region = FocusRegion(**request.model_dump())
        game.updated_at = datetime.now(timezone.utc)
        return self.store.save(game)
