<template>
  <section class="control-shell panel">
    <div class="title-row">
      <div>
        <p class="section-title">对局控制</p>
        <h2>棋盘上方操作区</h2>
      </div>
      <div class="status-row">
        <span class="chip">执棋：{{ colorLabel(session?.user_color) }}</span>
        <span class="chip">行棋方：{{ colorLabel(session?.board.to_play) }}</span>
        <span class="chip">状态：{{ statusLabel(session?.status) }}</span>
        <span class="chip">手数：{{ session?.move_history.length ?? 0 }}</span>
      </div>
    </div>

    <div class="control-grid">
      <div class="profile-row">
        <button
          v-for="profile in AI_PROFILES"
          :key="profile.value"
          class="profile-card"
          :class="{ active: aiProfile === profile.value }"
          type="button"
          @click="$emit('change-ai-profile', profile.value)"
        >
          <span class="profile-icon">{{ profile.icon }}</span>
          <div>
            <strong>{{ profile.label }}</strong>
            <p>{{ profile.description }}</p>
          </div>
        </button>
      </div>

      <div class="action-row">
        <button class="action-button" :disabled="creatingGame" @click="$emit('new-game')">
          {{ creatingGame ? "创建中..." : "新对局" }}
        </button>
        <button
          class="action-button secondary"
          :disabled="!session || session.status === 'finished' || session.status === 'resigned' || session.status === 'terminated'"
          @click="handleSuspendOrResume"
        >
          {{ session?.status === "suspended" ? "继续对局" : "挂起对局" }}
        </button>
        <button class="action-button secondary" :disabled="!canPlayAi || playingAi" @click="$emit('ai-move')">
          {{ playingAi ? "AI 应手中..." : "AI 应手" }}
        </button>
        <button
          class="action-button secondary"
          :disabled="!session || !['active', 'passed_once'].includes(session.status)"
          @click="$emit('pass')"
        >
          停一手
        </button>
        <button class="action-button ghost" :disabled="!session" @click="$emit('toggle-focus')">
          {{ focusMode ? "退出局部聚焦" : "局部聚焦" }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AiProfile, GameSession, GameStatus, StoneColor } from "@/types/game";

const props = defineProps<{
  aiProfile: AiProfile;
  canPlayAi: boolean;
  creatingGame: boolean;
  playingAi: boolean;
  focusMode: boolean;
  session: GameSession | null;
}>();

const emit = defineEmits<{
  (e: "change-ai-profile", value: AiProfile): void;
  (e: "new-game"): void;
  (e: "suspend"): void;
  (e: "resume-current"): void;
  (e: "ai-move"): void;
  (e: "pass"): void;
  (e: "toggle-focus"): void;
}>();

const AI_PROFILES: Array<{ value: AiProfile; icon: string; label: string; description: string }> = [
  {
    value: "companion",
    icon: "🐥",
    label: "陪练",
    description: "10岁左右，学棋 1 年内。优先软一点地应手，尽量让局面保持可学可下。",
  },
  {
    value: "teaching",
    icon: "🧭",
    label: "教学",
    description: "14岁左右，学棋 1 到 2 年。会认真下，但会保留讲解空间。",
  },
  {
    value: "serious",
    icon: "⚔",
    label: "认真下",
    description: "16岁左右，学棋 3 年以上。基本按强手来，适合挨打后复盘。",
  },
];

function handleSuspendOrResume() {
  if (props.session?.status === "suspended") {
    emit("resume-current");
    return;
  }
  emit("suspend");
}

function colorLabel(color?: StoneColor) {
  if (color === "black") return "黑棋";
  if (color === "white") return "白棋";
  return "未开始";
}

function statusLabel(status?: GameStatus) {
  if (status === "active") return "进行中";
  if (status === "passed_once") return "一方已停";
  if (status === "suspended") return "已挂起";
  if (status === "finished") return "正常结束";
  if (status === "resigned") return "认输结束";
  if (status === "terminated") return "强制终止";
  return "未开始";
}
</script>

<style scoped>
.control-shell {
  display: grid;
  gap: 16px;
  padding: 18px 20px;
  align-self: start;
}

.title-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.title-row h2 {
  margin: 6px 0 0;
  font-size: 24px;
}

.status-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.control-grid {
  display: grid;
  gap: 14px;
}

.profile-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.profile-card {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px;
  text-align: left;
  border-radius: 16px;
  border: 1px solid rgba(73, 61, 42, 0.14);
  background: rgba(255, 255, 255, 0.72);
}

.profile-card.active {
  border-color: rgba(23, 123, 107, 0.65);
  background: rgba(225, 247, 241, 0.92);
}

.profile-icon {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: rgba(36, 31, 24, 0.08);
}

.profile-card strong {
  display: block;
  margin-bottom: 4px;
}

.profile-card p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.35;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1120px) {
  .title-row {
    flex-direction: column;
  }

  .status-row {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .profile-row {
    grid-template-columns: 1fr;
  }
}
</style>
