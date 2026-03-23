from pydantic import BaseModel, Field


class KataGoTopMove(BaseModel):
    move: str
    visits: int = 0
    winrate: float | None = None
    score_lead: float | None = None
    prior: float | None = None
    order: int = 0
    pv: list[str] = Field(default_factory=list)


class KataGoAnalysisResult(BaseModel):
    turn_number: int
    winrate: float | None = None
    score_lead: float | None = None
    ownership: list[float] = Field(default_factory=list)
    top_moves: list[KataGoTopMove] = Field(default_factory=list)
