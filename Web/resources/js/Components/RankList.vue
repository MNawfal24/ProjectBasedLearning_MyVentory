<script setup>
import { computed } from 'vue';
import { formatNumber } from '../format';

const props = defineProps({
    items: { type: Array, required: true },
});

const max = computed(() => Math.max(1, ...props.items.map((item) => item.value)));
</script>

<template>
    <ol v-if="items.length" class="space-y-3">
        <li v-for="item in items" :key="item.label">
            <div class="flex items-baseline justify-between gap-3 text-body">
                <span class="truncate text-ink">{{ item.label }}</span>
                <span class="numeric shrink-0 text-2xs text-muted">{{ item.display ?? formatNumber(item.value) }}</span>
            </div>
            <div class="mt-1.5 h-1 overflow-hidden rounded-[2px] bg-surface-2">
                <div class="h-full rounded-[2px] bg-primary" :style="{ width: `${(item.value / max) * 100}%` }"></div>
            </div>
        </li>
    </ol>
    <p v-else class="py-8 text-center text-body text-muted">Belum ada penjualan pada periode ini.</p>
</template>