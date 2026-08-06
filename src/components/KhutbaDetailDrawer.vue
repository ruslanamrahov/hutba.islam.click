<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import AudioPlayer from './AudioPlayer.vue';

interface Khutba {
  number: string;
  title: string;
  year: number;
  category: string;
  audioUrl: string;
  textUrl: string;
  telegramUrl: string;
  pdfUrl: string;
  id: number;
}

const props = defineProps<{
  khutba: Khutba | null;
  categoryLabels: Record<string, string>;
}>();

const emit = defineEmits<{
  close: [];
}>();

const visible = ref(false);

watch(() => props.khutba, (val) => {
  if (val) {
    visible.value = true;
    document.body.style.overflow = 'hidden';
  }
});

function close() {
  visible.value = false;
  document.body.style.overflow = '';
  setTimeout(() => emit('close'), 300);
}

function onBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement).dataset.backdrop === 'true') {
    close();
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') close();
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown);
  document.body.style.overflow = '';
});
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="visible && khutba"
        data-backdrop="true"
        class="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
        @click="onBackdropClick"
      >
        <div class="absolute inset-y-0 right-0 w-full sm:w-[460px] bg-card shadow-2xl flex flex-col overflow-y-auto border-l border-border">
          <div class="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card/95 backdrop-blur px-5 py-4">
            <span class="text-xs font-medium text-muted-foreground">#{khutba.number}</span>
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
              aria-label="Закрыть"
              @click="close"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
              </svg>
            </button>
          </div>

          <div class="flex-1 px-5 py-6 space-y-6">
            <div class="flex flex-wrap items-center gap-2">
              <a
                :href="`/category/${khutba.category}`"
                class="inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary-foreground"
                :style="{ backgroundColor: `hsl(var(--cat-accent, var(--primary)))` }"
                :data-category="khutba.category"
              >{{ categoryLabels[khutba.category] || khutba.category }}</a>
              <span v-if="khutba.year > 0" class="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs text-secondary-foreground">
                {{ khutba.year < 2015 ? `До ${khutba.year}` : khutba.year }}
              </span>
            </div>

            <h2 class="text-xl font-bold tracking-tight text-foreground">{{ khutba.title }}</h2>

            <section>
              <h3 class="mb-3 text-sm font-medium text-muted-foreground">Аудиозапись</h3>
              <template v-if="khutba.audioUrl">
                <AudioPlayer :src="khutba.audioUrl" client:visible />
              </template>
              <a
                v-else-if="khutba.telegramUrl"
                :href="khutba.telegramUrl"
                target="_blank"
                rel="noopener"
                class="flex items-center gap-3 rounded-xl border border-border bg-card card-shadow p-4 transition-colors hover:border-primary"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0 text-muted-foreground"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                <div>
                  <div class="text-sm font-medium text-card-foreground">Слушать аудио в Telegram</div>
                  <div class="text-xs text-muted-foreground">Откроется во встроенном плеере</div>
                </div>
              </a>
              <p v-else class="text-sm text-muted-foreground">Аудиозапись недоступна</p>
            </section>

            <div class="grid gap-3 sm:grid-cols-2">
              <a
                v-if="khutba.textUrl"
                :href="khutba.textUrl"
                target="_blank"
                rel="noopener"
                class="flex items-center gap-3 rounded-xl border border-border bg-card card-shadow p-4 transition-colors hover:border-primary"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0 text-muted-foreground"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
                <div>
                  <div class="text-sm font-medium text-card-foreground">Читать текст</div>
                  <div class="text-xs text-muted-foreground">islam.click</div>
                </div>
              </a>

              <a
                v-if="khutba.pdfUrl"
                :href="khutba.pdfUrl"
                target="_blank"
                rel="noopener"
                class="flex items-center gap-3 rounded-xl border border-border bg-card card-shadow p-4 transition-colors hover:border-primary"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0 text-muted-foreground"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
                <div>
                  <div class="text-sm font-medium text-card-foreground">Скачать PDF</div>
                  <div class="text-xs text-muted-foreground">PDF</div>
                </div>
              </a>
            </div>

            <a
              :href="`/khutba/${khutba.id}`"
              class="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/></svg>
              Открыть на отдельной странице
            </a>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s ease;
}
.drawer-enter-active > div:last-child,
.drawer-leave-active > div:last-child {
  transition: transform 0.3s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > div:last-child {
  transform: translateX(100%);
}
.drawer-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
