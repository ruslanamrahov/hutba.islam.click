<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  src: string;
}>();

const audioRef = ref<HTMLAudioElement>();
const playing = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const error = ref(false);

function togglePlay() {
  if (!audioRef.value) return;
  if (audioRef.value.paused) {
    audioRef.value.play().catch(() => {
      error.value = true;
    });
  } else {
    audioRef.value.pause();
  }
}

function seek(e: Event) {
  const input = e.target as HTMLInputElement;
  if (!audioRef.value) return;
  audioRef.value.currentTime = Number(input.value);
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

function onTimeUpdate() {
  if (!audioRef.value) return;
  currentTime.value = audioRef.value.currentTime;
}

function onLoaded() {
  if (!audioRef.value) return;
  duration.value = audioRef.value.duration || 0;
}
</script>

<template>
  <div class="rounded-xl border border-border bg-card p-4">
    <div v-if="error" class="space-y-3">
      <p class="text-sm text-destructive">Не удалось загрузить аудиоплеер.</p>
      <a
        :href="src"
        target="_blank"
        rel="noopener"
        class="inline-flex items-center rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-card-foreground transition-colors hover:border-primary"
      >
        Скачать
      </a>
    </div>

    <template v-else>
      <audio
        ref="audioRef"
        :src="src"
        preload="metadata"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoaded"
        @play="playing = true"
        @pause="playing = false"
        @error="error = true"
        v-show="false"
      />

      <div class="flex items-center gap-3">
        <button
          type="button"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90"
          @click="togglePlay"
          :aria-label="playing ? 'Пауза' : 'Воспроизвести'"
        >
          <svg v-if="playing" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="6,3 20,12 6,21"/></svg>
        </button>

        <div class="flex flex-1 flex-col gap-1">
          <input
            type="range"
            :min="0"
            :max="duration || 0"
            :value="currentTime"
            @input="seek"
            class="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-secondary accent-primary"
          />
          <div class="flex justify-between text-xs text-muted-foreground">
            <span>{{ formatTime(currentTime) }}</span>
            <span>{{ formatTime(duration) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
