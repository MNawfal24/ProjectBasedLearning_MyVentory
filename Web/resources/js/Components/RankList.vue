<script setup>
import { computed } from 'vue';
import { formatNumber } from '../format';

const props = defineProps({
    items: { type: Array, required: true },
});

const max = computed(() => Math.max(1, ...props.items.map((item) => item.value)));
</script>

<template>
    <ul v-if="items.length" class="space-y-3">
        <li v-for="item in items" :key="item.label">
            <div class="flex items-baseline justify-between gap-3 text-sm">
                <span class="truncate text-ink">{{ item.label }}</span>
                <span class="numeric shrink-0 text-muted">{{ item.display ?? formatNumber(item.value) }}</span>
            </div>
            <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-2">
                <div class="h-full rounded-full bg-primary" :style="{ width: `${(item.value / max) * 100}%` }"></div>
            </div>
        </li>
    </ul>
    <p v-else class="py-6 text-center text-sm text-muted">Belum ada penjualan pada periode ini.</p>
</template>
