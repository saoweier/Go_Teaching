from fastapi import APIRouter, HTTPException

from app.dependencies import analysis_service, game_service, review_service
from app.domain.enums import MoveKind
from app.domain.models import (
    AnalysisRequest,
    AnalysisResultEnvelope,
    CreateGameRequest,
    FocusRegionRequest,
    GameSession,
    GameSummary,
    MoveRequest,
)
from app.domain.rules import IllegalMoveError
from app.engine.katago import KataGoUnavailableError
from app.services.game_service import GameNotFoundError


router = APIRouter(prefix="/api/games", tags=["games"])


def _load_game(game_id: str) -> GameSession:
    try:
        return game_service.get_game(game_id)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc


@router.post("", response_model=GameSession)
def create_game(request: CreateGameRequest) -> GameSession:
    return game_service.create_game(request)


@router.get("", response_model=list[GameSummary])
def list_games() -> list[GameSummary]:
    return game_service.list_games()


@router.get("/{game_id}", response_model=GameSession)
def get_game(game_id: str) -> GameSession:
    return _load_game(game_id)


@router.post("/{game_id}/moves", response_model=GameSession)
def play_user_move(game_id: str, request: MoveRequest) -> GameSession:
    game = _load_game(game_id)
    try:
        return game_service.apply_move(game_id, request, game.user_color)
    except IllegalMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{game_id}/moves/ai", response_model=GameSession)
def play_ai_move(game_id: str, request: AnalysisRequest) -> GameSession:
    game = _load_game(game_id)
    try:
        candidate = analysis_service.choose_ai_move(game, request)
        move_request = MoveRequest(point=candidate.move) if candidate.move else MoveRequest(kind=MoveKind.PASS)
        return game_service.apply_move(game_id, move_request, game.ai_color)
    except (IllegalMoveError, KataGoUnavailableError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{game_id}/analysis/current")
def analyze_current(game_id: str, request: AnalysisRequest) -> AnalysisResultEnvelope:
    game = _load_game(game_id)
    try:
        return analysis_service.analyze_current(game, request)
    except KataGoUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{game_id}/analysis/last-move")
def analyze_last_move(game_id: str, request: AnalysisRequest) -> AnalysisResultEnvelope:
    game = _load_game(game_id)
    try:
        return analysis_service.analyze_last_move(game, request)
    except KataGoUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{game_id}/analysis")
def list_analysis(game_id: str):
    game = _load_game(game_id)
    return {
        "analysis_snapshots": game.analysis_snapshots,
        "teaching_notes": game.teaching_notes,
    }


@router.post("/{game_id}/focus", response_model=GameSession)
def set_focus(game_id: str, request: FocusRegionRequest) -> GameSession:
    try:
        return game_service.set_focus_region(game_id, request)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{game_id}/focus")
def get_focus(game_id: str):
    game = _load_game(game_id)
    return {"focus_region": game.focus_region}


@router.post("/{game_id}/final-review")
def final_review(game_id: str):
    game = _load_game(game_id)
    return review_service.build_final_review(game)


@router.post("/{game_id}/suspend", response_model=GameSession)
def suspend_game(game_id: str) -> GameSession:
    try:
        return game_service.suspend_game(game_id)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc
    except IllegalMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{game_id}/resume", response_model=GameSession)
def resume_game(game_id: str) -> GameSession:
    try:
        return game_service.resume_game(game_id)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc
    except IllegalMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{game_id}/terminate")
def terminate_game(game_id: str):
    try:
        game = game_service.terminate_game(game_id)
        return {
            "game": game,
            "review": review_service.build_final_review(game),
        }
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc
    except IllegalMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
