<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import AccordionSection from './AccordionSection.vue';

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

const emit = defineEmits<{
  'select-khutba': [khutba: Khutba];
}>();

const activeTab = ref<'years' | 'categories'>('years');

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
const yearCategoriesExpanded = ref<Map<string, Set<string>>>(new Map());
const categoryYearsExpanded = ref<Map<string, Set<number>>>(new Map());

function getKhutbasForYear(year: number): Khutba[] {
  return props.khutbas
    .filter((k) => k.year === year)
    .sort((a, b) => parseInt(a.number) - parseInt(b.number));
}

function getCategoriesForYear(year: number) {
  const entries = getKhutbasForYear(year);
  const cats = [...new Set(entries.map((k) => k.category))];
  return cats.map((slug) => ({
    slug,
    label: props.categoryLabels[slug] || slug,
    count: entries.filter((k) => k.category === slug).length,
    khutbas: entries.filter((k) => k.category === slug),
    accent: categoryAccentHsl[slug] || '',
  }));
}

function getKhutbasForCategory(cat: string): Khutba[] {
  return props.khutbas
    .filter((k) => k.category === cat)
    .sort((a, b) => parseInt(a.number) - parseInt(b.number));
}

function getYearsForCategory(cat: string) {
  const entries = getKhutbasForCategory(cat);
  const yrs = [...new Set(entries.map((k) => k.year))]
    .filter((y) => y !== 0)
    .sort((a, b) => a - b);
  return yrs.map((year) => ({
    year,
    count: entries.filter((k) => k.year === year).length,
    khutbas: entries.filter((k) => k.year === year),
  }));
}

function toggleYear(year: number) {
  const s = new Set(expandedYears.value);
  if (s.has(year)) {
    s.delete(year);
  } else {
    s.add(year);
  }
  expandedYears.value = s;
}

function toggleCategory(cat: string) {
  const s = new Set(expandedCategories.value);
  if (s.has(cat)) {
    s.delete(cat);
  } else {
    s.add(cat);
  }
  expandedCategories.value = s;
}

function toggleYearCategory(year: number, cat: string) {
  const key = String(year);
  const map = new Map(yearCategoriesExpanded.value);
  if (!map.has(key)) map.set(key, new Set());
  const inner = new Set(map.get(key)!);
  if (inner.has(cat)) {
    inner.delete(cat);
  } else {
    inner.add(cat);
  }
  map.set(key, inner);
  yearCategoriesExpanded.value = map;
}

function isYearCategoryExpanded(year: number, cat: string): boolean {
  const key = String(year);
  return yearCategoriesExpanded.value.get(key)?.has(cat) ?? false;
}

function toggleCategoryYear(cat: string, year: number) {
  const map = new Map(categoryYearsExpanded.value);
  if (!map.has(cat)) map.set(cat, new Set());
  const inner = new Set(map.get(cat)!);
  if (inner.has(year)) {
    inner.delete(year);
  } else {
    inner.add(year);
  }
  map.set(cat, inner);
  categoryYearsExpanded.value = map;
}

function isCategoryYearExpanded(cat: string, year: number): boolean {
  return categoryYearsExpanded.value.get(cat)?.has(year) ?? false;
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
      <div v-for="year in years" :key="year" :id="`year-${year}`" class="rounded-xl border border-border bg-card card-shadow overflow-hidden">
        <AccordionSection
          :title="year < 2015 ? `До ${year}` : `${year} год`"
          :count="getKhutbasForYear(year).length"
          :expanded="expandedYears.has(year)"
          @toggle="toggleYear(year); writeHash('year', String(year))"
        >
          <div class="space-y-1">
            <div v-for="cat in getCategoriesForYear(year)" :key="cat.slug">
              <AccordionSection
                :title="cat.label"
                :count="cat.count"
                :accent-hsl="cat.accent"
                :expanded="isYearCategoryExpanded(year, cat.slug)"
                :level="1"
                @toggle="toggleYearCategory(year, cat.slug)"
              >
                <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <button
                    v-for="k in cat.khutbas"
                    :key="k.id"
                    type="button"
                    class="group flex flex-col gap-2 text-left rounded-[14px] border-2 border-transparent bg-card card-shadow p-4 transition-colors duration-200 hover:cat-accent-border focus-visible:cat-accent-border focus-visible:outline-none w-full"
                    :style="{ '--cat-accent': `hsl(${cat.accent})` }"
                    @click="emit('select-khutba', k)"
                  >
                    <div class="flex items-start justify-between gap-2">
                      <span class="text-xs font-medium text-muted-foreground tabular-nums">#{{ k.number }}</span>
                    </div>
                    <h3 class="text-sm font-semibold leading-snug text-card-foreground">{{ k.title }}</h3>
                    <div class="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{{ k.year }}</span>
                      <span v-if="k.audioUrl" class="cat-accent-text">&bull; Аудио</span>
                      <span v-if="k.textUrl">&bull; Текст</span>
                    </div>
                  </button>
                </div>
              </AccordionSection>
            </div>
          </div>
        </AccordionSection>
      </div>
    </div>

    <div v-show="activeTab === 'categories'" role="tabpanel" class="space-y-2">
      <div v-for="cat in categories" :key="cat.slug" :id="`cat-${cat.slug}`" class="rounded-xl border border-border bg-card card-shadow overflow-hidden">
        <AccordionSection
          :title="cat.label"
          :count="cat.count"
          :accent-hsl="cat.accent"
          :expanded="expandedCategories.has(cat.slug)"
          @toggle="toggleCategory(cat.slug); writeHash('cat', cat.slug)"
        >
          <div class="space-y-1">
            <div v-for="yr in getYearsForCategory(cat.slug)" :key="yr.year">
              <AccordionSection
                :title="yr.year < 2015 ? `До ${yr.year}` : `${yr.year} год`"
                :count="yr.count"
                :expanded="isCategoryYearExpanded(cat.slug, yr.year)"
                :level="1"
                @toggle="toggleCategoryYear(cat.slug, yr.year)"
              >
                <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <button
                    v-for="k in yr.khutbas"
                    :key="k.id"
                    type="button"
                    class="group flex flex-col gap-2 text-left rounded-[14px] border-2 border-transparent bg-card card-shadow p-4 transition-colors duration-200 hover:cat-accent-border focus-visible:cat-accent-border focus-visible:outline-none w-full"
                    :style="{ '--cat-accent': `hsl(${cat.accent})` }"
                    @click="emit('select-khutba', k)"
                  >
                    <div class="flex items-start justify-between gap-2">
                      <span class="text-xs font-medium text-muted-foreground tabular-nums">#{{ k.number }}</span>
                    </div>
                    <h3 class="text-sm font-semibold leading-snug text-card-foreground">{{ k.title }}</h3>
                    <div class="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{{ k.year }}</span>
                      <span v-if="k.audioUrl" class="cat-accent-text">&bull; Аудио</span>
                      <span v-if="k.textUrl">&bull; Текст</span>
                    </div>
                  </button>
                </div>
              </AccordionSection>
            </div>
          </div>
        </AccordionSection>
      </div>
    </div>
  </div>
</template>
