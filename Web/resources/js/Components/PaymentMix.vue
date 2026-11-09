<script setup>
import { computed } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { formatNumber } from '../format';

const props = defineProps({
    items: { type: Array, required: true },
});

const total = computed(() => props.items.reduce((sum, item) => sum + item.transactions, 0));
</script>

<template>
    <div v-if="items.length">
        <div class="flex h-3 overflow-hidden rounded-full bg-surface-2" role="img" aria-label="Porsi metode pembayaran">
            <div
                v-for="(item, index) in items"
                :key="item.method"
                :style="{ width: `${item.share}%`, opacity: 1 - index * 0.22 }"
                class="h-full bg-primary"
                :title="`${item.method}: ${item.share}%`"
            ></div>
        </div>

        <ul class="mt-4 space-y-2.5">
            <li v-for="(item, index) in items" :key="item.method" class="flex items-center justify-between gap-3 text-sm">
                <span class="flex items-center gap-2 text-ink">
                    <span class="h-2.5 w-2.5 rounded-sm bg-primary" :style="{ opacity: 1 - index * 0.22 }"></span>
                    {{ item.method }}
                </span>
                <span class="flex items-center gap-2">
                    <span class="numeric text-xs text-muted">{{ formatNumber(item.transactions) }} struk</span>
                    <Badge variant="secondary" class="numeric">{{ String(item.share).replace('.', ',') }}%</Badge>
                </span>
            </li>
        </ul>
        <p class="mt-3 text-xs text-muted">Total {{ formatNumber(total) }} struk pada periode ini.</p>
    </div>
    <p v-else class="py-6 text-center text-sm text-muted">Belum ada data pembayaran.</p>
</template>
