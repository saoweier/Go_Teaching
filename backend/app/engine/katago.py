from __future__ import annotations

import json
import subprocess
import threading
import time
import uuid
from collections import deque
from pathlib import Path

from app.config import settings
from app.domain.enums import MoveKind
from app.domain.models import GameSession, Point
from app.engine.schemas import KataGoAnalysisResult, KataGoTopMove


class KataGoUnavailableError(RuntimeError):
    pass


class KataGoAnalysisEngine:
    def __init__(self, executable: Path, model: Path, config: Path):
        self.executable = executable
        self.model = model
        self.config = config
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._stderr_lines: deque[str] = deque(maxlen=40)
        self._stdout_log_lines: deque[str] = deque(maxlen=80)
        self._stderr_thread: threading.Thread | None = None
        self._ready_event = threading.Event()

    def start(self) -> None:
        if self._process and self._process.poll() is None:
            return
        if not self.executable.exists():
            raise KataGoUnavailableError(f"KataGo executable not found: {self.executable}")
        if not self.model.exists():
            raise KataGoUnavailableError(f"KataGo model not found: {self.model}")
        if not self.config.exists():
            raise KataGoUnavailableError(f"KataGo config not found: {self.config}")

        self._stderr_lines.clear()
        self._stdout_log_lines.clear()
        self._ready_event.clear()
        self._process = subprocess.Popen(
            [
                str(self.executable),
                "analysis",
                "-model",
                str(self.model),
                "-config",
                str(self.config),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=str(settings.katago_executable.parent),
            bufsize=1,
        )
        self._start_stderr_reader()
        self._wait_until_ready()

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait(timeout=5)
        self._process = None

    def _start_stderr_reader(self) -> None:
        if not self._process or self._process.stderr is None:
            return

        def _reader() -> None:
            assert self._process is not None
            assert self._process.stderr is not None
            for line in self._process.stderr:
                cleaned = line.strip()
                if cleaned:
                    self._stderr_lines.append(cleaned)
                    if "Started, ready to begin handling requests" in cleaned:
                        self._ready_event.set()

        self._stderr_thread = threading.Thread(target=_reader, daemon=True)
        self._stderr_thread.start()

    def _wait_until_ready(self, timeout_seconds: float = 20.0) -> None:
        process = self._process
        if process is None:
            raise KataGoUnavailableError("KataGo process is not available")

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if self._ready_event.wait(timeout=0.1):
                return
            if process.poll() is not None:
                raise KataGoUnavailableError(self._build_process_failure_message("KataGo exited during startup"))

        raise KataGoUnavailableError(self._build_process_failure_message("KataGo did not become ready in time"))

    def _ensure_started(self) -> subprocess.Popen[str]:
        self.start()
        assert self._process is not None
        return self._process

    def analyze(self, game: GameSession, max_visits: int | None = None, include_ownership: bool = True) -> KataGoAnalysisResult:
        request_id = str(uuid.uuid4())
        payload = {
            "id": request_id,
            "boardXSize": game.board_size,
            "boardYSize": game.board_size,
            "rules": game.rules,
            "komi": game.komi,
            "moves": self._serialize_moves(game),
            "analyzeTurns": [len(game.move_history)],
            "includeOwnership": include_ownership,
        }
        if max_visits is not None:
            payload["maxVisits"] = max_visits

        with self._lock:
            process = self._ensure_started()
            if process.stdin is None or process.stdout is None:
                raise KataGoUnavailableError("KataGo process streams are not available")

            try:
                process.stdin.write(json.dumps(payload) + "\n")
                process.stdin.flush()
            except OSError as exc:
                self.stop()
                raise KataGoUnavailableError(self._build_process_failure_message(f"Failed to send request to KataGo: {exc}")) from exc

            while True:
                if process.poll() is not None:
                    self.stop()
                    raise KataGoUnavailableError(self._build_process_failure_message("KataGo analysis process exited unexpectedly"))

                line = process.stdout.readline()
                if not line:
                    continue
                cleaned = line.strip()
                if not cleaned:
                    continue

                try:
                    data = json.loads(cleaned)
                except json.JSONDecodeError:
                    self._stdout_log_lines.append(cleaned)
                    continue

                if data.get("id") != request_id:
                    continue
                return self._parse_response(data, len(game.move_history))

    def _build_process_failure_message(self, prefix: str) -> str:
        stderr_summary = " | ".join(list(self._stderr_lines)[-5:])
        stdout_summary = " | ".join(list(self._stdout_log_lines)[-5:])
        details = []
        if stderr_summary:
          details.append(f"stderr: {stderr_summary}")
        if stdout_summary:
          details.append(f"stdout: {stdout_summary}")
        suffix = f" ({'; '.join(details)})" if details else ""
        return f"{prefix}{suffix}"

    @staticmethod
    def _serialize_moves(game: GameSession) -> list[list[str]]:
        items: list[list[str]] = []
        for move in game.move_history:
            if move.kind == MoveKind.PLAY and move.point:
                items.append([move.color.katago_code, point_to_gtp(move.point, game.board_size)])
            elif move.kind == MoveKind.PASS:
                items.append([move.color.katago_code, "pass"])
        return items

    @staticmethod
    def _parse_response(data: dict, turn_number: int) -> KataGoAnalysisResult:
        root_info = data.get("rootInfo", {})
        move_infos = data.get("moveInfos", [])
        top_moves = [
            KataGoTopMove(
                move=item.get("move", "pass"),
                visits=item.get("visits", 0),
                winrate=item.get("winrate"),
                score_lead=item.get("scoreLead"),
                prior=item.get("prior"),
                order=item.get("order", 0),
                pv=item.get("pv", []),
            )
            for item in move_infos[:8]
        ]
        return KataGoAnalysisResult(
            turn_number=turn_number,
            winrate=root_info.get("winrate"),
            score_lead=root_info.get("scoreLead"),
            ownership=data.get("ownership", []),
            top_moves=top_moves,
        )


GTP_COLUMNS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


def point_to_gtp(point: Point, board_size: int) -> str:
    return f"{GTP_COLUMNS[point.col]}{board_size - point.row}"


def gtp_to_point(value: str, board_size: int) -> Point | None:
    if value.lower() == "pass":
        return None
    col = GTP_COLUMNS.index(value[0].upper())
    row = board_size - int(value[1:])
    return Point(row=row, col=col)
