<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import AccordionSection from './AccordionSection.vue';
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
  khutbas: Khutba[];
  categoryLabels: Record<string, string>;
}>();

const activeTab = ref<'years' | 'categories'>('years');

const expandedPlayerId = ref<number | null>(null);

function togglePlayer(id: number) {
  expandedPlayerId.value = expandedPlayerId.value === id ? null : id;
}

const categoryAccentHsl: Record<string, string> = {
  'ramadan': '35 92% 50%',
  'sira': '142.1 70.6% 45.3%',
  'companions': '175 84% 32%',
  'zul-hijjah': '0 72% 51%',
  'muharram': '239 84% 67%',
  'mawlid': '271 81% 56%',
  'aqida': '215 19% 35%',
  'names-of-allah': '160 84% 39%',
  'shaban': '199 89% 48%',
  'new-year': '347 77% 50%',
  'forbidden-deeds': '25 95% 53%',
  'general': '142.1 70.6% 45.3%',
};

const years = computed(() => {
  return [...new Set(props.khutbas.map((k) => k.year))]
    .filter((y) => y !== 0)
    .sort((a, b) => a - b);
});

const categories = computed(() => {
  const slugs = [...new Set(props.khutbas.map((k) => k.category))];
  return slugs.map((slug) => ({
    slug,
    label: props.categoryLabels[slug] || slug,
    count: props.khutbas.filter((k) => k.category === slug).length,
    accent: categoryAccentHsl[slug] || '',
  }));
});

const expandedYears = ref<Set<number>>(new Set());
const expandedCategories = ref<Set<string>>(new Set());

function getKhutbasForYear(year: number): Khutba[] {
  return props.khutbas
    .filter((k) => k.year === year)
    .sort((a, b) => parseInt(a.number) - parseInt(b.number));
}

function getKhutbasForCategory(cat: string): Khutba[] {
  return props.khutbas
    .filter((k) => k.category === cat)
    .sort((a, b) => parseInt(a.number) - parseInt(b.number));
}

function toggleYear(year: number) {
  const s = new Set(expandedYears.value);
  if (s.has(year)) s.delete(year);
  else s.add(year);
  expandedYears.value = s;
}

function toggleCategory(cat: string) {
  const s = new Set(expandedCategories.value);
  if (s.has(cat)) s.delete(cat);
  else s.add(cat);
  expandedCategories.value = s;
}

function yearLabel(y: number): string {
  return y < 2015 ? `До ${y + 1}` : `${y} год`;
}

function handleHash() {
  const hash = window.location.hash;
  if (!hash) return;
  const match = hash.match(/^#year-(\d+)$/);
  if (match) {
    const y = parseInt(match[1]);
    expandedYears.value = new Set([y]);
    activeTab.value = 'years';
    setTimeout(() => {
      document.getElementById(`year-${y}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
  const catMatch = hash.match(/^#cat-(.+)$/);
  if (catMatch) {
    const c = catMatch[1];
    expandedCategories.value = new Set([c]);
    activeTab.value = 'categories';
    setTimeout(() => {
      document.getElementById(`cat-${c}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
}

function writeHash(prefix: string, value: string) {
  history.replaceState(null, '', `#${prefix}-${value}`);
}

onMounted(() => {
  handleHash();
  window.addEventListener('hashchange', handleHash);
});

watch(activeTab, () => {
  history.replaceState(null, '', window.location.pathname);
});
</script>

<template>
  <div id="browse" class="space-y-6">
    <div class="flex rounded-xl border border-border bg-card p-1" role="tablist" aria-label="Режим просмотра">
      <button
        role="tab"
        :aria-selected="activeTab === 'years'"
        class="flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors"
        :class="activeTab === 'years' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'years'"
      >По годам</button>
      <button
        role="tab"
        :aria-selected="activeTab === 'categories'"
        class="flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors"
        :class="activeTab === 'categories' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'categories'"
      >По темам</button>
    </div>

    <div v-show="activeTab === 'years'" role="tabpanel" class="space-y-2">
      <div
        v-for="year in years"
        :key="year"
        :id="`year-${year}`"
        class="rounded-xl border border-border bg-card card-shadow overflow-hidden"
      >
        <AccordionSection
          :title="yearLabel(year)"
          :count="getKhutbasForYear(year).length"
          :expanded="expandedYears.has(year)"
          @toggle="toggleYear(year); writeHash('year', String(year))"
        >
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 items-start">
            <div
              v-for="k in getKhutbasForYear(year)"
              :key="k.id"
              :data-category="k.category"
              class="rounded-[14px] border-2 border-transparent bg-card card-shadow p-4"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span class="shrink-0 text-xs font-medium text-muted-foreground tabular-nums">#{{ k.number }}</span>
                <button
                  type="button"
                  class="flex items-center gap-1.5 min-w-0 flex-1 text-left cursor-pointer group/title"
                  @click="togglePlayer(k.id)"
                >
                  <h3 class="text-sm font-semibold leading-snug text-card-foreground group-hover/title:text-primary transition-colors" :class="expandedPlayerId === k.id ? '' : 'truncate'">{{ k.title }}</h3>
                  <svg v-if="k.audioUrl || k.telegramUrl" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                       class="shrink-0 text-muted-foreground transition-transform duration-200"
                       :class="expandedPlayerId === k.id ? 'rotate-180' : ''">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                <span
                  class="shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary-foreground cat-accent-bg"
                >{{ categoryLabels[k.category] || k.category }}</span>
                <a
                  v-if="k.pdfUrl"
                  :href="k.pdfUrl"
                  target="_blank"
                  rel="noopener"
                  class="shrink-0 text-muted-foreground hover:text-primary transition-colors"
                  title="Скачать PDF"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/></svg>
                </a>
                <a :href="`/khutba/${k.id}`" class="shrink-0 text-muted-foreground hover:text-foreground transition-colors" title="Подробнее">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/></svg>
                </a>
              </div>

              <div v-if="expandedPlayerId === k.id" class="mt-3">
                <AudioPlayer v-if="k.audioUrl" :src="k.audioUrl" preload="none" />
                <a
                  v-else-if="k.telegramUrl"
                  :href="k.telegramUrl"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:border-primary transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                  Слушать в Telegram
                </a>
              </div>
            </div>
          </div>
        </AccordionSection>
      </div>
    </div>

    <div v-show="activeTab === 'categories'" role="tabpanel" class="space-y-2">
      <div
        v-for="cat in categories"
        :key="cat.slug"
        :id="`cat-${cat.slug}`"
        class="rounded-xl border border-border bg-card card-shadow overflow-hidden"
      >
        <AccordionSection
          :title="cat.label"
          :count="cat.count"
          :accent-hsl="cat.accent"
          :expanded="expandedCategories.has(cat.slug)"
          @toggle="toggleCategory(cat.slug); writeHash('cat', cat.slug)"
        >
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 items-start">
            <div
              v-for="k in getKhutbasForCategory(cat.slug)"
              :key="k.id"
              :data-category="k.category"
              class="rounded-[14px] border-2 border-transparent bg-card card-shadow p-4"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span class="shrink-0 text-xs font-medium text-muted-foreground tabular-nums">#{{ k.number }}</span>
                <button
                  type="button"
                  class="flex items-center gap-1.5 min-w-0 flex-1 text-left cursor-pointer group/title"
                  @click="togglePlayer(k.id)"
                >
                  <h3 class="text-sm font-semibold leading-snug text-card-foreground group-hover/title:text-primary transition-colors" :class="expandedPlayerId === k.id ? '' : 'truncate'">{{ k.title }}</h3>
                  <svg v-if="k.audioUrl || k.telegramUrl" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                       class="shrink-0 text-muted-foreground transition-transform duration-200"
                       :class="expandedPlayerId === k.id ? 'rotate-180' : ''">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                <span class="inline-flex shrink-0 items-center rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
                  {{ k.year > 0 ? (k.year < 2015 ? `До ${k.year + 1}` : k.year) : '' }}
                </span>
                <a
                  v-if="k.pdfUrl"
                  :href="k.pdfUrl"
                  target="_blank"
                  rel="noopener"
                  class="shrink-0 text-muted-foreground hover:text-primary transition-colors"
                  title="Скачать PDF"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/></svg>
                </a>
                <a :href="`/khutba/${k.id}`" class="shrink-0 text-muted-foreground hover:text-foreground transition-colors" title="Подробнее">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/></svg>
                </a>
              </div>

              <div v-if="expandedPlayerId === k.id" class="mt-3">
                <AudioPlayer v-if="k.audioUrl" :src="k.audioUrl" preload="none" />
                <a
                  v-else-if="k.telegramUrl"
                  :href="k.telegramUrl"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:border-primary transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                  Слушать в Telegram
                </a>
              </div>
            </div>
          </div>
        </AccordionSection>
      </div>
    </div>
  </div>
</template>
