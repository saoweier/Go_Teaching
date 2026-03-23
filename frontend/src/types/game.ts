export type StoneColor = "black" | "white";
export type MoveKind = "play" | "pass" | "resign";
export type GameStatus = "active" | "passed_once" | "finished" | "resigned";
export type AiProfile = "companion" | "teaching" | "serious";

export interface Point {
  row: number;
  col: number;
}

export interface FocusRegion {
  top: number;
  left: number;
  height: number;
  width: number;
}

export interface MoveRecord {
  move_number: number;
  color: StoneColor;
  kind: MoveKind;
  point: Point | null;
  captured_points: Point[];
  board_hash: string;
  created_at: string;
}

export interface CandidateMove {
  move: Point | null;
  move_gtp: string;
  visits: number;
  winrate: number | null;
  score_lead: number | null;
  prior: number | null;
  order: number;
  pv: string[];
}

export interface TeachingSummary {
  headline: string;
  key_points: string[];
  recommended_direction: string | null;
  why_this_move: string | null;
  impact_summary: string | null;
  future_sequence: string[];
  profile: AiProfile;
}

export interface AnalysisSnapshot {
  request_type: "current" | "last_move" | "bot_move";
  target_move_number: number;
  winrate: number | null;
  score_lead: number | null;
  ownership_map: number[];
  top_moves: CandidateMove[];
  created_at: string;
}

export interface TeachingNote {
  request_type: "current" | "last_move" | "bot_move" | "final_review";
  target_move_number: number;
  summary: TeachingSummary;
  created_at: string;
}

export interface AnalysisResultEnvelope {
  analysis: AnalysisSnapshot;
  teaching_note: TeachingNote | null;
}

export interface BoardState {
  size: number;
  grid: string[][];
  to_play: StoneColor;
  ko_point: Point | null;
  captures: Record<StoneColor, number>;
}

export interface GameSession {
  id: string;
  board_size: number;
  user_color: StoneColor;
  ai_color: StoneColor;
  status: GameStatus;
  komi: number;
  rules: string;
  board: BoardState;
  focus_region: FocusRegion | null;
  move_history: MoveRecord[];
  analysis_snapshots: AnalysisSnapshot[];
  teaching_notes: TeachingNote[];
  created_at: string;
  updated_at: string;
}

export interface FinalReview {
  status: "estimated" | "requires_analysis";
  territory_estimate_black: number;
  territory_estimate_white: number;
  capture_count_black: number;
  capture_count_white: number;
  key_moments: string[];
  teaching_summary: string;
}
