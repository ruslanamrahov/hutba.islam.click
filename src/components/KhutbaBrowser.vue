<script setup lang="ts">
import { ref } from 'vue';
import KhutbaAccordion from './KhutbaAccordion.vue';
import KhutbaDetailDrawer from './KhutbaDetailDrawer.vue';

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

const selectedKhutba = ref<Khutba | null>(null);

function onSelect(khutba: Khutba) {
  selectedKhutba.value = khutba;
}

function onClose() {
  selectedKhutba.value = null;
}
</script>

<template>
  <KhutbaAccordion
    :khutbas="khutbas"
    :category-labels="categoryLabels"
    @select-khutba="onSelect"
  />
  <KhutbaDetailDrawer
    :khutba="selectedKhutba"
    :category-labels="categoryLabels"
    @close="onClose"
  />
</template>
