<template>
  <header class="topbar panel">
    <div class="brand-row">
      <div class="brand-block">
        <div class="brand-mark">围</div>
        <div>
          <h1>围棋教学工作台</h1>
          <p>把对弈、分析和教学拆成更清晰的操作区。</p>
        </div>
      </div>

      <div class="status-row">
        <span class="chip">执棋：{{ colorLabel(session?.user_color) }}</span>
        <span class="chip">行棋方：{{ colorLabel(session?.board.to_play) }}</span>
        <span class="chip">状态：{{ statusLabel(session?.status) }}</span>
        <span class="chip">手数：{{ session?.move_history.length ?? 0 }}</span>
      </div>
    </div>

    <div class="toolbar-grid">
      <section class="tool-group ai-group">
        <p class="group-label">AI 档位</p>
        <div class="profile-grid">
          <button
            v-for="profile in AI_PROFILES"
            :key="profile.value"
            class="profile-card"
            :class="{ active: aiProfile === profile.value }"
            type="button"
            @click="$emit('change-ai-profile', profile.value)"
          >
            <div class="profile-head">
              <span class="profile-icon">{{ profile.icon }}</span>
              <strong>{{ profile.label }}</strong>
            </div>
            <p>{{ profile.description }}</p>
          </button>
        </div>
      </section>

      <section class="tool-group">
        <p class="group-label">对局</p>
        <div class="group-actions">
          <button class="action-button" :disabled="creatingGame" @click="$emit('new-game')">
            {{ creatingGame ? "创建中..." : "新对局" }}
          </button>
          <button class="action-button secondary" :disabled="!canPlayAi || playingAi" @click="$emit('ai-move')">
            {{ playingAi ? "AI 应手中..." : "AI 应手" }}
          </button>
          <button class="action-button secondary" :disabled="!session" @click="$emit('pass')">
            停一手
          </button>
        </div>
      </section>

      <section class="tool-group">
        <p class="group-label">教学分析</p>
        <div class="group-actions">
          <button class="action-button secondary" :disabled="!canAnalyze || analyzing" @click="$emit('analyze')">
            {{ analyzing ? "分析中..." : "分析当前局面" }}
          </button>
          <button class="action-button secondary" :disabled="!canAnalyze || analyzing" @click="$emit('analyze-last-move')">
            分析上一手
          </button>
        </div>
      </section>

      <section class="tool-group utility-group">
        <p class="group-label">视图与终局</p>
        <div class="group-actions">
          <button class="action-button ghost" :disabled="!session" @click="$emit('toggle-focus')">
            {{ focusMode ? "退出局部聚焦" : "局部聚焦" }}
          </button>
          <button class="action-button ghost" :disabled="!session || reviewing" @click="$emit('final-review')">
            {{ reviewing ? "生成中..." : "终局复盘" }}
          </button>
          <button class="text-button danger" :disabled="!session" @click="$emit('resign')">
            认输
          </button>
        </div>
      </section>
    </div>
  </header>
</template>

<script setup lang="ts">
import type { AiProfile, GameSession, GameStatus, StoneColor } from "@/types/game";

defineProps<{
  aiProfile: AiProfile;
  canAnalyze: boolean;
  canPlayAi: boolean;
  creatingGame: boolean;
  analyzing: boolean;
  playingAi: boolean;
  reviewing: boolean;
  focusMode: boolean;
  session: GameSession | null;
}>();

defineEmits<{
  (e: "change-ai-profile", value: AiProfile): void;
  (e: "new-game"): void;
  (e: "analyze"): void;
  (e: "analyze-last-move"): void;
  (e: "ai-move"): void;
  (e: "pass"): void;
  (e: "resign"): void;
  (e: "toggle-focus"): void;
  (e: "final-review"): void;
}>();

const AI_PROFILES: Array<{ value: AiProfile; icon: string; label: string; description: string }> = [
  {
    value: "companion",
    icon: "🐢",
    label: "陪练",
    description: "下得像在等你想明白，不急着一拳把你送走。",
  },
  {
    value: "teaching",
    icon: "🧭",
    label: "教学",
    description: "大体合理，偶尔留点空间，让你看懂局面起伏。",
  },
  {
    value: "serious",
    icon: "⚔",
    label: "认真下",
    description: "少讲情面，基本按强手来，适合挨打时复盘。",
  },
];

function colorLabel(color?: StoneColor) {
  if (color === "black") return "黑棋";
  if (color === "white") return "白棋";
  return "未开始";
}

function statusLabel(status?: GameStatus) {
  if (status === "active") return "进行中";
  if (status === "passed_once") return "一方停一手";
  if (status === "finished") return "已结束";
  if (status === "resigned") return "认输结束";
  return "-";
}
</script>

<style scoped>
.topbar {
  display: grid;
  gap: 20px;
  padding: 22px 24px;
}

.brand-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-block h1 {
  margin: 0;
  font-size: 28px;
}

.brand-block p {
  margin: 4px 0 0;
  color: var(--muted);
}

.brand-mark {
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: linear-gradient(135deg, #2d2117, #8a6640);
  color: #fff7eb;
  font-size: 24px;
  font-weight: 700;
}

.status-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr 1fr 1fr;
  gap: 14px;
}

.tool-group {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(73, 61, 42, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(255, 248, 238, 0.9));
}

.group-label {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}

.group-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.profile-card {
  display: grid;
  gap: 8px;
  padding: 12px 12px 14px;
  text-align: left;
  border-radius: 16px;
  border: 1px solid rgba(73, 61, 42, 0.14);
  background: rgba(255, 255, 255, 0.72);
  transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
}

.profile-card:hover {
  transform: translateY(-1px);
  border-color: rgba(23, 123, 107, 0.35);
}

.profile-card.active {
  border-color: rgba(23, 123, 107, 0.65);
  background: rgba(225, 247, 241, 0.9);
  box-shadow: inset 0 0 0 1px rgba(23, 123, 107, 0.18);
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-icon {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: rgba(36, 31, 24, 0.08);
  font-size: 16px;
}

.profile-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: var(--muted);
}

.utility-group {
  align-content: start;
}

.text-button {
  padding: 12px 4px;
  background: transparent;
  color: var(--muted);
  font-weight: 600;
}

.text-button.danger {
  color: var(--danger);
}

@media (max-width: 1320px) {
  .toolbar-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 1160px) {
  .brand-row {
    flex-direction: column;
  }

  .status-row {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .toolbar-grid,
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
