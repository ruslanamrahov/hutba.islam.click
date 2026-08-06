<script setup lang="ts">
import { ref, watch } from 'vue';

const props = withDefaults(defineProps<{
  title: string;
  count?: number;
  expanded?: boolean;
  accentHsl?: string;
  level?: number;
}>(), {
  count: 0,
  expanded: false,
  accentHsl: '',
  level: 0,
});

const emit = defineEmits<{
  toggle: [];
}>();

const isOpen = ref(props.expanded);
const contentRef = ref<HTMLElement>();

watch(() => props.expanded, (val) => {
  isOpen.value = val;
});

function handleToggle() {
  isOpen.value = !isOpen.value;
  emit('toggle');
}
</script>

<template>
  <div class="accordion-section" :class="{ 'is-open': isOpen }">
    <button
      type="button"
      class="w-full flex items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-accent/50 rounded-xl group"
      :class="level === 0 ? '' : 'pl-8'"
      :aria-expanded="isOpen"
      @click="handleToggle"
      :style="accentHsl ? { '--cat-accent': accentHsl } : {}"
    >
      <span class="flex-1 min-w-0">
        <span
          class="text-sm font-semibold text-card-foreground"
          :class="{ 'cat-accent-text': !!accentHsl }"
        >{{ title }}</span>
      </span>
      <span
        v-if="count > 0"
        class="shrink-0 rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground"
      >{{ count }}</span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="shrink-0 text-muted-foreground transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
      >
        <path d="m6 9 6 6 6-6"/>
      </svg>
    </button>
    <div
      ref="contentRef"
      class="grid transition-all duration-300 ease-in-out"
      :class="isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
    >
      <div class="overflow-hidden">
        <div class="pb-2" :class="level === 0 ? 'pl-0' : 'pl-6'">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>
