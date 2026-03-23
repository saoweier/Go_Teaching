from app.domain.models import CandidateMove, GameSession, Point, TeachingSummary


class TeachingService:
    def build_summary(
        self,
        game: GameSession,
        top_moves: list[CandidateMove],
        winrate: float | None,
        score_lead: float | None,
        ai_profile: str,
    ) -> TeachingSummary:
        if not top_moves:
            return TeachingSummary(
                headline="当前无法获取稳定分析结果",
                key_points=["请稍后重试，或降低并发分析请求。"],
                why_this_move="分析引擎暂时没有给出足够稳定的候选手。",
                profile=ai_profile,  # type: ignore[arg-type]
            )

        best = top_moves[0]
        direction = self._describe_point(best.move, game.board_size)
        score_text = self._describe_score(score_lead)
        reason = self._build_reason(best, direction)
        impact = self._build_impact(direction, score_text)
        future = self._build_future_sequence(top_moves, direction)

        if ai_profile == "companion":
            headline = f"先在{direction}附近补一手更稳" if direction else "先把局面走稳"
            key_points = [
                reason,
                impact,
            ]
            return TeachingSummary(
                headline=headline,
                key_points=key_points,
                recommended_direction=direction,
                why_this_move="这一步带一点让手意味，先顺着局部补形，不急着马上抓你刚露出的漏洞。",
                impact_summary=impact,
                future_sequence=future[:2],
                profile="companion",
            )

        if ai_profile == "serious":
            headline = f"当前效率最高的点在{direction}" if direction else "当前效率最高的是先手整理"
            key_points = []
            if winrate is not None:
                key_points.append(f"当前参考胜率约为 {winrate:.1%}。")
            if score_lead is not None:
                key_points.append(f"目差趋势约为 {score_lead:+.1f}。")
            key_points.append(reason)
            key_points.append(impact)
            if len(top_moves) > 1:
                key_points.append("若改走次选点，局部厚薄和先后手关系会更差一些。")
            return TeachingSummary(
                headline=headline,
                key_points=key_points,
                recommended_direction=direction,
                why_this_move="这一步优先考虑效率、先后手和局部厚薄，不刻意给对手留缓冲。",
                impact_summary=impact,
                future_sequence=future,
                profile="serious",
            )

        headline = f"当前建议优先考虑{direction}" if direction else "当前建议先手整理局面"
        key_points = []
        if winrate is not None:
            key_points.append(f"当前参考胜率约为 {winrate:.1%}。")
        if score_lead is not None:
            key_points.append(f"目差趋势约为 {score_lead:+.1f}。")
        key_points.append(reason)
        key_points.append(impact)
        if len(top_moves) > 1:
            key_points.append("建议至少比较前两手变化，不要只盯着一个数字。")
        return TeachingSummary(
            headline=headline,
            key_points=key_points,
            recommended_direction=direction,
            why_this_move="这一步通常兼顾了局部稳定和后续发展空间，适合教学场景讲清楚来龙去脉。",
            impact_summary=impact,
            future_sequence=future[:3],
            profile="teaching",
        )

    @staticmethod
    def _describe_point(point: Point | None, board_size: int) -> str | None:
        if point is None:
            return "停一手"
        vertical = "上方" if point.row < board_size // 3 else "下方" if point.row >= (board_size * 2) // 3 else "中腹"
        horizontal = "左侧" if point.col < board_size // 3 else "右侧" if point.col >= (board_size * 2) // 3 else "中央"
        return f"{vertical}{horizontal}"

    @staticmethod
    def _build_reason(best: CandidateMove, direction: str | None) -> str:
        if direction is None:
            return "这里优先处理先后手关系，避免无效纠缠。"
        if best.score_lead is not None and best.score_lead > 0:
            return f"走在{direction}更像是在稳住主动权，不急着冒险扩大。"
        if best.score_lead is not None and best.score_lead < 0:
            return f"走在{direction}是在补局面的薄味，先把容易出事的地方压住。"
        return f"走在{direction}可以同时照顾形状和出路，通常比单纯抢空更均衡。"

    @staticmethod
    def _build_impact(direction: str | None, score_text: str) -> str:
        if direction is None:
            return f"这手对后续的影响主要是整理收束，{score_text}。"
        return f"如果这里先落子，后面局面大多会朝着{direction}一带更稳定、对手选择更少的方向发展，{score_text}。"

    @staticmethod
    def _build_future_sequence(top_moves: list[CandidateMove], direction: str | None) -> list[str]:
        if not top_moves:
            return []

        best = top_moves[0]
        if best.pv:
            sequence: list[str] = []
            for index, move in enumerate(best.pv[:4], start=1):
                if index == 1:
                    sequence.append(f"第{index}步通常先走 {move}，先把主要矛盾落在盘上。")
                elif index == 2:
                    sequence.append(f"第{index}步对手多半会在 {move} 一带应对，试图争先或补断点。")
                elif index == 3:
                    sequence.append(f"第{index}步再走 {move}，常见目的是把形状走厚，减少后续变数。")
                else:
                    sequence.append(f"再往后若走到 {move}，这一串变化大致就会转成可控局面。")
            return sequence

        if direction is None:
            return [
                "接下来通常会先把最紧的断点或出路补上。",
                "对手如果不理，会让你顺手把局面整理干净。",
            ]

        return [
            f"先在{direction}落子后，下一步通常会围绕附近的薄味继续处理。",
            "对手多半会补强、反夹或争先，局面不会立刻打成大转换。",
            "如果两边都稳住，后续就会回到更大的全局点。 ",
        ]

    @staticmethod
    def _describe_score(score_lead: float | None) -> str:
        if score_lead is None:
            return "现在更该看局部稳定，而不是死盯数字"
        if score_lead > 3:
            return "说明这手偏向稳住已有优势"
        if score_lead < -3:
            return "说明这手偏向止损和补强"
        return "说明这一带主要是在争局面的厚薄与节奏"
