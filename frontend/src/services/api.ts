import type {
  AiProfile,
  AnalysisResultEnvelope,
  FinalReview,
  FocusRegion,
  GameSummary,
  GameSession,
  Point,
  StoneColor,
  TerminateGameResponse,
} from "@/types/game";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function createGame(payload: {
  board_size: number;
  user_color: StoneColor;
  komi: number;
  rules: string;
}) {
  return request<GameSession>("/api/games", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listGames() {
  return request<GameSummary[]>("/api/games");
}

export function loadGame(gameId: string) {
  return request<GameSession>(`/api/games/${gameId}`);
}

export function playMove(gameId: string, payload: { kind: "play" | "pass" | "resign"; point?: Point }) {
  return request<GameSession>(`/api/games/${gameId}/moves`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function requestAiMove(
  gameId: string,
  payload: { max_visits: number; include_ownership: boolean; include_pv: boolean; ai_profile: AiProfile },
) {
  return request<GameSession>(`/api/games/${gameId}/moves/ai`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function analyzeCurrent(
  gameId: string,
  payload: { max_visits: number; include_ownership: boolean; include_pv: boolean; ai_profile: AiProfile },
) {
  return request<AnalysisResultEnvelope>(`/api/games/${gameId}/analysis/current`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function analyzeLastMove(
  gameId: string,
  payload: { max_visits: number; include_ownership: boolean; include_pv: boolean; ai_profile: AiProfile },
) {
  return request<AnalysisResultEnvelope>(`/api/games/${gameId}/analysis/last-move`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loadAnalysisHistory(gameId: string) {
  return request<{ analysis_snapshots: AnalysisResultEnvelope["analysis"][]; teaching_notes: AnalysisResultEnvelope["teaching_note"][] }>(
    `/api/games/${gameId}/analysis`,
  );
}

export function setFocusRegion(gameId: string, payload: FocusRegion) {
  return request<GameSession>(`/api/games/${gameId}/focus`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loadFinalReview(gameId: string) {
  return request<FinalReview>(`/api/games/${gameId}/final-review`, {
    method: "POST",
  });
}

export function suspendGame(gameId: string) {
  return request<GameSession>(`/api/games/${gameId}/suspend`, {
    method: "POST",
  });
}

export function resumeGame(gameId: string) {
  return request<GameSession>(`/api/games/${gameId}/resume`, {
    method: "POST",
  });
}

export function terminateGame(gameId: string) {
  return request<TerminateGameResponse>(`/api/games/${gameId}/terminate`, {
    method: "POST",
  });
}
