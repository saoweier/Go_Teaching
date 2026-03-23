from app.domain.enums import GameStatus, ReviewStatus, StoneColor
from app.domain.models import FinalReview, GameSession


class ReviewService:
    def build_final_review(self, game: GameSession) -> FinalReview:
        black_stones = sum(cell == "B" for row in game.board.grid for cell in row)
        white_stones = sum(cell == "W" for row in game.board.grid for cell in row)
        black_score = black_stones + game.board.captures[StoneColor.BLACK]
        white_score = white_stones + game.board.captures[StoneColor.WHITE] + game.komi

        key_moments: list[str] = []
        if game.analysis_snapshots:
            key_moments.append("对局过程中已经产生分析快照，可优先回看关键节点。")
        if len(game.move_history) >= 2:
            key_moments.append("建议复盘最后 10 手，确认是否还有未收完的官子或死活残留。")

        if game.status == GameStatus.RESIGNED:
            resign_color = game.move_history[-1].color if game.move_history else game.user_color
            winner = "黑方" if resign_color == StoneColor.WHITE else "白方"
            loser = "黑方" if resign_color == StoneColor.BLACK else "白方"
            key_moments.insert(0, f"本局以{loser}认输结束，形式上由{winner}获胜。")
            teaching_summary = (
                "这是认输局的教学复盘。重点不在点目精度，而在回看认输前局面是否已经明显失衡，"
                "以及是否还有更稳的简化手段可以选择。"
            )
        else:
            teaching_summary = "这是估算式终局总结，适合教学回看，但不替代严格点目和完整死活判定。"

        return FinalReview(
            status=ReviewStatus.ESTIMATED,
            territory_estimate_black=float(black_score),
            territory_estimate_white=float(white_score),
            capture_count_black=game.board.captures[StoneColor.BLACK],
            capture_count_white=game.board.captures[StoneColor.WHITE],
            key_moments=key_moments,
            teaching_summary=teaching_summary,
        )
