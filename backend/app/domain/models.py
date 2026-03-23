from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import GameStatus, MoveKind, ReviewStatus, StoneColor


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Point(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)


class FocusRegion(BaseModel):
    top: int = Field(ge=0)
    left: int = Field(ge=0)
    height: int = Field(gt=0)
    width: int = Field(gt=0)


class MoveRecord(BaseModel):
    move_number: int = Field(ge=1)
    color: StoneColor
    kind: MoveKind
    point: Point | None = None
    captured_points: list[Point] = Field(default_factory=list)
    board_hash: str
    created_at: datetime = Field(default_factory=utc_now)


class CandidateMove(BaseModel):
    move: Point | None = None
    move_gtp: str
    visits: int = 0
    winrate: float | None = None
    score_lead: float | None = None
    prior: float | None = None
    order: int = 0
    pv: list[str] = Field(default_factory=list)


class TeachingSummary(BaseModel):
    headline: str
    key_points: list[str] = Field(default_factory=list)
    recommended_direction: str | None = None
    why_this_move: str | None = None
    impact_summary: str | None = None
    future_sequence: list[str] = Field(default_factory=list)
    profile: Literal["companion", "teaching", "serious"] = "teaching"


class AnalysisSnapshot(BaseModel):
    request_type: Literal["current", "last_move", "bot_move"]
    target_move_number: int = Field(ge=0)
    winrate: float | None = None
    score_lead: float | None = None
    ownership_map: list[float] = Field(default_factory=list)
    top_moves: list[CandidateMove] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class TeachingNote(BaseModel):
    request_type: Literal["current", "last_move", "bot_move", "final_review"]
    target_move_number: int = Field(ge=0)
    summary: TeachingSummary
    created_at: datetime = Field(default_factory=utc_now)


class AnalysisResultEnvelope(BaseModel):
    analysis: AnalysisSnapshot
    teaching_note: TeachingNote | None = None


class BoardState(BaseModel):
    size: int = Field(ge=5, le=25)
    grid: list[list[str]]
    to_play: StoneColor
    ko_point: Point | None = None
    captures: dict[StoneColor, int] = Field(
        default_factory=lambda: {StoneColor.BLACK: 0, StoneColor.WHITE: 0}
    )
    model_config = ConfigDict(use_enum_values=False)


class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    board_size: int
    user_color: StoneColor
    ai_color: StoneColor
    status: GameStatus = GameStatus.ACTIVE
    komi: float = 7.5
    rules: str = "tromp-taylor"
    board: BoardState
    focus_region: FocusRegion | None = None
    move_history: list[MoveRecord] = Field(default_factory=list)
    analysis_snapshots: list[AnalysisSnapshot] = Field(default_factory=list)
    teaching_notes: list[TeachingNote] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CreateGameRequest(BaseModel):
    board_size: int = Field(default=19, ge=5, le=25)
    user_color: StoneColor = StoneColor.BLACK
    komi: float = 7.5
    rules: str = "tromp-taylor"


class MoveRequest(BaseModel):
    kind: MoveKind = MoveKind.PLAY
    point: Point | None = None


class FocusRegionRequest(BaseModel):
    top: int = Field(ge=0)
    left: int = Field(ge=0)
    height: int = Field(gt=0)
    width: int = Field(gt=0)


class AnalysisRequest(BaseModel):
    max_visits: int | None = Field(default=None, gt=0)
    include_ownership: bool = True
    include_pv: bool = True
    ai_profile: Literal["companion", "teaching", "serious"] = "teaching"


class FinalReview(BaseModel):
    status: ReviewStatus
    territory_estimate_black: float
    territory_estimate_white: float
    capture_count_black: int
    capture_count_white: int
    key_moments: list[str] = Field(default_factory=list)
    teaching_summary: str
