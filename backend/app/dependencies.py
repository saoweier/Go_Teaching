from app.config import settings
from app.engine.katago import KataGoAnalysisEngine
from app.services.analysis_service import AnalysisService
from app.services.game_service import GameService
from app.services.review_service import ReviewService
from app.services.teaching_service import TeachingService
from app.stores.game_store import InMemoryGameStore


game_store = InMemoryGameStore()
game_service = GameService(game_store)
teaching_service = TeachingService()
katago_engine = KataGoAnalysisEngine(
    executable=settings.katago_executable,
    model=settings.katago_model,
    config=settings.katago_analysis_config,
)
analysis_service = AnalysisService(katago_engine, teaching_service)
review_service = ReviewService()
