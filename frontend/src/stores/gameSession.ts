import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  analyzeCurrent,
  analyzeLastMove,
  createGame,
  loadAnalysisHistory,
  loadFinalReview,
  loadGame,
  playMove,
  requestAiMove,
  setFocusRegion,
} from "@/services/api";
import type {
  AiProfile,
  AnalysisResultEnvelope,
  AnalysisSnapshot,
  FinalReview,
  FocusRegion,
  GameSession,
  Point,
  StoneColor,
  TeachingNote,
} from "@/types/game";

const ACTIVE_GAME_KEY = "go-teaching-active-game-id";
const AI_PROFILE_KEY = "go-teaching-ai-profile";
const AUTO_ANALYZE_KEY = "go-teaching-auto-analyze";

const AI_PROFILE_VISITS: Record<AiProfile, number> = {
  companion: 40,
  teaching: 90,
  serious: 220,
};

export const useGameSessionStore = defineStore("gameSession", () => {
  const gameSession = ref<GameSession | null>(null);
  const analysisHistory = ref<AnalysisSnapshot[]>([]);
  const teachingHistory = ref<TeachingNote[]>([]);
  const currentAnalysis = ref<AnalysisSnapshot | null>(null);
  const currentTeachingNote = ref<TeachingNote | null>(null);
  const finalReview = ref<FinalReview | null>(null);
  const aiProfile = ref<AiProfile>("teaching");
  const autoAnalyzeEnabled = ref(true);

  const isCreatingGame = ref(false);
  const isAnalyzing = ref(false);
  const isPlayingAiMove = ref(false);
  const isGeneratingFinalReview = ref(false);
  const lastError = ref<string | null>(null);
  const isAnalysisStale = ref(false);

  const hasGame = computed(() => Boolean(gameSession.value));
  const canAnalyze = computed(() => Boolean(gameSession.value));
  const canPlayAiMove = computed(() => Boolean(gameSession.value));
  const isMyTurn = computed(() => gameSession.value?.board.to_play === gameSession.value?.user_color);

  function resetSessionState() {
    gameSession.value = null;
    analysisHistory.value = [];
    teachingHistory.value = [];
    currentAnalysis.value = null;
    currentTeachingNote.value = null;
    finalReview.value = null;
    isAnalysisStale.value = false;
  }

  function persistActiveGame() {
    if (typeof window === "undefined") return;
    if (gameSession.value?.id) {
      window.localStorage.setItem(ACTIVE_GAME_KEY, gameSession.value.id);
    }
  }

  function clearPersistedActiveGame() {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(ACTIVE_GAME_KEY);
  }

  function persistAiProfile() {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(AI_PROFILE_KEY, aiProfile.value);
  }

  function persistAutoAnalyze() {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(AUTO_ANALYZE_KEY, String(autoAnalyzeEnabled.value));
  }

  function restorePreferences() {
    if (typeof window === "undefined") return;

    const persistedProfile = window.localStorage.getItem(AI_PROFILE_KEY);
    if (persistedProfile === "companion" || persistedProfile === "teaching" || persistedProfile === "serious") {
      aiProfile.value = persistedProfile;
    }

    const persistedAutoAnalyze = window.localStorage.getItem(AUTO_ANALYZE_KEY);
    if (persistedAutoAnalyze === "true" || persistedAutoAnalyze === "false") {
      autoAnalyzeEnabled.value = persistedAutoAnalyze === "true";
    }
  }

  function pushEnvelope(envelope: AnalysisResultEnvelope) {
    currentAnalysis.value = envelope.analysis;
    currentTeachingNote.value = envelope.teaching_note;
    analysisHistory.value = [...analysisHistory.value, envelope.analysis];
    if (envelope.teaching_note) {
      teachingHistory.value = [...teachingHistory.value, envelope.teaching_note];
    }
    isAnalysisStale.value = false;
  }

  async function createNewGame(userColor: StoneColor) {
    isCreatingGame.value = true;
    lastError.value = null;
    try {
      const session = await createGame({
        board_size: 19,
        user_color: userColor,
        komi: 7.5,
        rules: "tromp-taylor",
      });
      resetSessionState();
      gameSession.value = session;
      persistActiveGame();
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : "创建棋局失败";
      throw error;
    } finally {
      isCreatingGame.value = false;
    }
  }

  async function restoreGame(gameId: string) {
    lastError.value = null;
    try {
      const [session, history] = await Promise.all([loadGame(gameId), loadAnalysisHistory(gameId)]);
      gameSession.value = session;
      persistActiveGame();
      analysisHistory.value = history.analysis_snapshots;
      teachingHistory.value = history.teaching_notes.filter(Boolean) as TeachingNote[];
      currentAnalysis.value = analysisHistory.value.at(-1) ?? null;
      currentTeachingNote.value = teachingHistory.value.at(-1) ?? null;
      isAnalysisStale.value = false;
    } catch (error) {
      const handled = handleMissingGame(error, "之前的对局已经失效，已为你清空本地记录。请新开一局。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "恢复棋局失败";
      }
      throw error;
    }
  }

  async function submitMove(point: Point) {
    if (!gameSession.value) return;
    if (!isMyTurn.value) {
      lastError.value = "现在不是你的回合，请等待 AI 应手。";
      return;
    }

    lastError.value = null;
    try {
      gameSession.value = await playMove(gameSession.value.id, { kind: "play", point });
      persistActiveGame();
      isAnalysisStale.value = true;
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "落子失败";
      }
      throw error;
    }
  }

  async function requestCurrentAnalysis() {
    if (!gameSession.value) return;
    isAnalyzing.value = true;
    lastError.value = null;
    try {
      const envelope = await analyzeCurrent(gameSession.value.id, {
        max_visits: 260,
        include_ownership: true,
        include_pv: true,
        ai_profile: aiProfile.value,
      });
      pushEnvelope(envelope);
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "分析失败";
      }
      throw error;
    } finally {
      isAnalyzing.value = false;
    }
  }

  async function requestLastMoveAnalysis() {
    if (!gameSession.value) return;
    isAnalyzing.value = true;
    lastError.value = null;
    try {
      const envelope = await analyzeLastMove(gameSession.value.id, {
        max_visits: 220,
        include_ownership: true,
        include_pv: true,
        ai_profile: aiProfile.value,
      });
      pushEnvelope(envelope);
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "上一手分析失败";
      }
      throw error;
    } finally {
      isAnalyzing.value = false;
    }
  }

  async function maybeAutoAnalyze() {
    if (!autoAnalyzeEnabled.value || !gameSession.value) {
      return;
    }
    await requestCurrentAnalysis();
  }

  async function playAiTurn() {
    if (!gameSession.value) return;
    isPlayingAiMove.value = true;
    lastError.value = null;
    try {
      gameSession.value = await requestAiMove(gameSession.value.id, {
        max_visits: AI_PROFILE_VISITS[aiProfile.value],
        include_ownership: false,
        include_pv: true,
        ai_profile: aiProfile.value,
      });
      persistActiveGame();
      isAnalysisStale.value = true;
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "AI 应手失败";
      }
      throw error;
    } finally {
      isPlayingAiMove.value = false;
    }
  }

  async function submitMoveThenAi(point: Point) {
    await submitMove(point);
    if (!gameSession.value || isMyTurn.value) {
      return;
    }
    await playAiTurn();
    await maybeAutoAnalyze();
  }

  async function playAiTurnAndAnalyze() {
    await playAiTurn();
    await maybeAutoAnalyze();
  }

  async function updateFocusRegion(region: FocusRegion) {
    if (!gameSession.value) return;
    lastError.value = null;
    try {
      gameSession.value = await setFocusRegion(gameSession.value.id, region);
      persistActiveGame();
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "设置聚焦区域失败";
      }
      throw error;
    }
  }

  async function generateFinalReview() {
    if (!gameSession.value) return;
    isGeneratingFinalReview.value = true;
    lastError.value = null;
    try {
      finalReview.value = await loadFinalReview(gameSession.value.id);
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "终局复盘失败";
      }
      throw error;
    } finally {
      isGeneratingFinalReview.value = false;
    }
  }

  async function submitPass() {
    if (!gameSession.value) return;
    if (!isMyTurn.value) {
      lastError.value = "现在不是你的回合，不能停一手。";
      return;
    }
    lastError.value = null;
    try {
      gameSession.value = await playMove(gameSession.value.id, { kind: "pass" });
      persistActiveGame();
      isAnalysisStale.value = true;
      await maybeAutoAnalyze();
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "停一手失败";
      }
      throw error;
    }
  }

  async function submitResign() {
    if (!gameSession.value) return;
    lastError.value = null;
    try {
      gameSession.value = await playMove(gameSession.value.id, { kind: "resign" });
      persistActiveGame();
      isAnalysisStale.value = true;
    } catch (error) {
      const handled = handleMissingGame(error, "当前对局在后端已不存在，已清空本地记录。请重新开始。");
      if (!handled) {
        lastError.value = error instanceof Error ? error.message : "认输失败";
      }
      throw error;
    }
  }

  async function submitResignAndReview() {
    await submitResign();
    await generateFinalReview();
  }

  function setAiProfile(profile: AiProfile) {
    aiProfile.value = profile;
    persistAiProfile();
  }

  function toggleAutoAnalyze() {
    autoAnalyzeEnabled.value = !autoAnalyzeEnabled.value;
    persistAutoAnalyze();
  }

  function getPersistedGameId() {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(ACTIVE_GAME_KEY);
  }

  function handleMissingGame(error: unknown, fallbackMessage: string) {
    if (!(error instanceof Error)) return false;
    if (!error.message.includes("Game not found")) return false;
    clearPersistedActiveGame();
    resetSessionState();
    lastError.value = fallbackMessage;
    return true;
  }

  restorePreferences();

  return {
    aiProfile,
    analysisHistory,
    autoAnalyzeEnabled,
    canAnalyze,
    canPlayAiMove,
    createNewGame,
    currentAnalysis,
    currentTeachingNote,
    finalReview,
    gameSession,
    generateFinalReview,
    getPersistedGameId,
    hasGame,
    isAnalyzing,
    isAnalysisStale,
    isCreatingGame,
    isGeneratingFinalReview,
    isMyTurn,
    isPlayingAiMove,
    lastError,
    playAiTurn,
    playAiTurnAndAnalyze,
    requestCurrentAnalysis,
    requestLastMoveAnalysis,
    restoreGame,
    setAiProfile,
    submitMove,
    submitMoveThenAi,
    submitPass,
    submitResign,
    submitResignAndReview,
    teachingHistory,
    toggleAutoAnalyze,
    updateFocusRegion,
  };
});
