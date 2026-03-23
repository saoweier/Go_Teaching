from app.domain.models import GameSession


class InMemoryGameStore:
    def __init__(self) -> None:
        self._games: dict[str, GameSession] = {}

    def save(self, game: GameSession) -> GameSession:
        self._games[game.id] = game
        return game

    def get(self, game_id: str) -> GameSession | None:
        return self._games.get(game_id)
