from enum import Enum


class StoneColor(str, Enum):
    BLACK = "black"
    WHITE = "white"

    @property
    def opposite(self) -> "StoneColor":
        return StoneColor.WHITE if self == StoneColor.BLACK else StoneColor.BLACK

    @property
    def katago_code(self) -> str:
        return "B" if self == StoneColor.BLACK else "W"


class GameStatus(str, Enum):
    ACTIVE = "active"
    PASSED_ONCE = "passed_once"
    SUSPENDED = "suspended"
    FINISHED = "finished"
    RESIGNED = "resigned"
    TERMINATED = "terminated"


class MoveKind(str, Enum):
    PLAY = "play"
    PASS = "pass"
    RESIGN = "resign"


class ReviewStatus(str, Enum):
    ESTIMATED = "estimated"
    REQUIRES_ANALYSIS = "requires_analysis"
