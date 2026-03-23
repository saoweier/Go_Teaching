from app.domain.enums import MoveKind
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
        move_count = len(game.move_history)
        phase = self._describe_phase(move_count)
        pace = self._describe_pace(score_lead)
        local_fight = self._detect_local_skirmish(game)

        if local_fight["active"]:
            return self._build_local_fight_summary(
                ai_profile=ai_profile,
                phase=phase,
                pace=pace,
                direction=direction,
                local_fight=local_fight,
                winrate=winrate,
                score_lead=score_lead,
            )

        strategic_advice = self._build_strategic_advice(move_count, score_lead)
        tenuki_advice = self._build_tenuki_advice(move_count, score_lead)
        why = self._build_macro_why(direction, phase, ai_profile)
        impact = self._build_macro_impact(direction, pace)

        if ai_profile == "companion":
            return TeachingSummary(
                headline=f"现在更重要的是先把{phase}走稳",
                key_points=[
                    f"全局节奏偏向{pace}，先确认这一带有没有明显薄味。",
                    strategic_advice,
                    tenuki_advice,
                ],
                recommended_direction=direction,
                why_this_move=why,
                impact_summary=impact,
                future_sequence=[],
                profile="companion",
            )

        if ai_profile == "serious":
            points = [
                f"当前局势属于{phase}，判断重点是先后手和大场价值。",
                strategic_advice,
                tenuki_advice,
            ]
            if winrate is not None:
                points.append(f"当前参考胜率约为 {winrate:.1%}。")
            if score_lead is not None:
                points.append(f"目差趋势约为 {score_lead:+.1f}。")
            return TeachingSummary(
                headline=f"从全局看，当前更应优先处理{phase}里的关键方向",
                key_points=points,
                recommended_direction=direction,
                why_this_move=why,
                impact_summary=impact,
                future_sequence=[],
                profile="serious",
            )

        return TeachingSummary(
            headline="当前要先判断是继续局部作战，还是转向更大的全局点",
            key_points=[
                f"局面阶段属于{phase}，不能只盯着局部一块棋。",
                strategic_advice,
                tenuki_advice,
            ],
            recommended_direction=direction,
            why_this_move=why,
            impact_summary=impact,
            future_sequence=[],
            profile="teaching",
        )

    def _build_local_fight_summary(
        self,
        ai_profile: str,
        phase: str,
        pace: str,
        direction: str | None,
        local_fight: dict,
        winrate: float | None,
        score_lead: float | None,
    ) -> TeachingSummary:
        zone = local_fight["zone"]
        zone_label = self._describe_zone(zone)
        headline = f"这一带还在局部摩擦，先判断{zone_label}要不要继续应战"
        why = self._build_local_why(ai_profile, zone_label, pace)
        impact = self._build_local_impact(zone_label, pace)

        base_points = [
            f"最近几手主要集中在{zone_label}，这更像是局部战斗而不是单纯的大局转场。",
            self._build_local_strategic_advice(score_lead),
            self._build_local_tenuki_advice(score_lead),
        ]

        if ai_profile == "companion":
            return TeachingSummary(
                headline=headline,
                key_points=base_points,
                recommended_direction=direction,
                why_this_move=why,
                impact_summary=impact,
                future_sequence=[],
                profile="companion",
            )

        if ai_profile == "serious":
            points = [f"当前虽然属于{phase}，但最近几手已经把焦点拉回到{zone_label}这一带。", *base_points[1:]]
            if winrate is not None:
                points.append(f"当前参考胜率约为 {winrate:.1%}。")
            if score_lead is not None:
                points.append(f"目差趋势约为 {score_lead:+.1f}。")
            return TeachingSummary(
                headline=headline,
                key_points=points,
                recommended_direction=direction,
                why_this_move=why,
                impact_summary=impact,
                future_sequence=[],
                profile="serious",
            )

        return TeachingSummary(
            headline=headline,
            key_points=base_points,
            recommended_direction=direction,
            why_this_move=why,
            impact_summary=impact,
            future_sequence=[],
            profile="teaching",
        )

    @staticmethod
    def _detect_local_skirmish(game: GameSession) -> dict:
        recent_plays = [
            move.point
            for move in game.move_history[-8:]
            if move.kind == MoveKind.PLAY and move.point is not None
        ]
        if len(recent_plays) < 4:
            return {"active": False}

        rows = [point.row for point in recent_plays]
        cols = [point.col for point in recent_plays]
        row_span = max(rows) - min(rows)
        col_span = max(cols) - min(cols)
        active = row_span <= 6 and col_span <= 6
        return {
            "active": active,
            "zone": {
                "top": min(rows),
                "bottom": max(rows),
                "left": min(cols),
                "right": max(cols),
            },
        }

    @staticmethod
    def _describe_point(point: Point | None, board_size: int) -> str | None:
        if point is None:
            return "停一手"
        vertical = "上方" if point.row < board_size // 3 else "下方" if point.row >= (board_size * 2) // 3 else "中腹"
        horizontal = "左侧" if point.col < board_size // 3 else "右侧" if point.col >= (board_size * 2) // 3 else "中央"
        return f"{vertical}{horizontal}"

    @staticmethod
    def _describe_zone(zone: dict) -> str:
        row_mid = (zone["top"] + zone["bottom"]) / 2
        col_mid = (zone["left"] + zone["right"]) / 2
        vertical = "上方" if row_mid < 6 else "下方" if row_mid >= 12 else "中腹"
        horizontal = "左侧" if col_mid < 6 else "右侧" if col_mid >= 12 else "中央"
        return f"{vertical}{horizontal}"

    @staticmethod
    def _describe_phase(move_count: int) -> str:
        if move_count < 30:
            return "布局阶段"
        if move_count < 120:
            return "中盘阶段"
        return "收束阶段"

    @staticmethod
    def _describe_pace(score_lead: float | None) -> str:
        if score_lead is None:
            return "均衡"
        if score_lead > 3:
            return "稳住优势"
        if score_lead < -3:
            return "先止损补强"
        return "拉锯均衡"

    @staticmethod
    def _build_strategic_advice(move_count: int, score_lead: float | None) -> str:
        if move_count < 30:
            return "布局阶段优先比较边角和大场价值，如果局部没有立即出棋的风险，可以把目光放到更大的空点。"
        if score_lead is not None and score_lead > 3:
            return "当前若已稍占上风，建议更多考虑稳住厚薄和先后手，不必为了多抢一点眼前利益把局面再度搅乱。"
        if score_lead is not None and score_lead < -3:
            return "当前局面若已落后，重点不是到处抢，而是先选一块最容易补强、最容易争回节奏的地方。"
        return "中盘阶段要同时看局部战斗和全局效率，不能只在一处缠斗到把大场全部放掉。"

    @staticmethod
    def _build_tenuki_advice(move_count: int, score_lead: float | None) -> str:
        if move_count < 30:
            return "如果这一带已经没有明显断点和死活压力，可以考虑脱先，把战斗转到更大的方向。"
        if score_lead is not None and score_lead > 3:
            return "若本地已经走厚，脱先去别处抢先手通常比继续压榨局部更划算。"
        if score_lead is not None and score_lead < -3:
            return "若本地还没彻底安定，不建议轻易脱先；先把最危险的一口气或断点看清楚。"
        return "判断是否脱先的核心，不是看这手漂不漂亮，而是看本地是否还存在会被对手立刻利用的薄味。"

    @staticmethod
    def _build_local_strategic_advice(score_lead: float | None) -> str:
        if score_lead is not None and score_lead > 3:
            return "如果你这一块已经不太会出事，继续在这里硬压未必最值钱，先想清楚能不能借厚味脱先。"
        if score_lead is not None and score_lead < -3:
            return "如果这一块还在被追着打，先把断点、气紧和出头问题处理掉，比抢别处更急。"
        return "这类小规模摩擦里，先判断谁的棋更薄、谁还没安定，再决定要不要继续打下去。"

    @staticmethod
    def _build_local_tenuki_advice(score_lead: float | None) -> str:
        if score_lead is not None and score_lead > 3:
            return "若本地已经基本安定，可以认真考虑脱先，到别处抢更大的收益点。"
        if score_lead is not None and score_lead < -3:
            return "若本地还有被切断、被压缩眼位或被追杀的风险，就暂时不要脱先。"
        return "如果本地只剩官子级别的小便宜，通常可以脱先；如果还牵涉断点和死活，就应该继续留在局部。"

    @staticmethod
    def _build_macro_why(direction: str | None, phase: str, ai_profile: str) -> str:
        if ai_profile == "companion":
            return f"这一步主要是帮助你把{phase}里的关键一带先走稳，不强调立刻局部获利。"
        if direction is None:
            return "这一步更偏向整理全局节奏，先判断该不该继续局部作战。"
        return f"这一步落在{direction}，重点不是这个点本身，而是借它决定全局接下来是继续局部作战还是转向其他方向。"

    @staticmethod
    def _build_macro_impact(direction: str | None, pace: str) -> str:
        if direction is None:
            return f"这手的全局意义更偏向节奏转换，决定接下来是否适合脱先，整体目标是{pace}。"
        return f"这手对后势的价值，在于让{direction}一带先变得更可控，从而决定下一拍是继续留在局部战斗，还是转去别处抢更大的点；整体目标是{pace}。"

    @staticmethod
    def _build_local_why(ai_profile: str, zone_label: str, pace: str) -> str:
        if ai_profile == "companion":
            return f"这一步主要是先把{zone_label}这一带的局部关系看清楚，不急着把小摩擦一下子升级成大混战。"
        return f"这一步的核心不是局部手筋本身，而是判断{zone_label}这一带是否已经可以告一段落，还是还必须继续应战；整体目标是{pace}。"

    @staticmethod
    def _build_local_impact(zone_label: str, pace: str) -> str:
        return f"这手对后势的影响，在于决定{zone_label}这一带是继续缠斗、转换成先手收束，还是直接脱先转战别处；整体目标是{pace}。"
