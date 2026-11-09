<script setup>
import { computed } from 'vue';
import Icon from './Icon.vue';

const props = defineProps({
    items: { type: Array, required: true },
});

const cells = computed(() =>
    props.items.map((item) => {
        const change = item.change_pct;
        const positive = change !== null && change >= 0;

        return {
            ...item,
            positive,
            delta: change === null ? null : `${positive ? '+' : ''}${String(change).replace('.', ',')}%`,
        };
    }),
);

function cellClass(index) {
    return [
        'px-5 py-4',
        index >= 2 ? 'border-t border-line lg:border-t-0' : '',
        index % 2 === 1 ? 'border-l border-line' : '',
        index >= 1 ? 'lg:border-l lg:border-line' : '',
    ];
}
</script>

<template>
    <div class="grid grid-cols-2 rounded-xl border border-line bg-surface lg:grid-cols-4">
        <div v-for="(cell, index) in cells" :key="cell.label" :class="cellClass(index)">
            <p class="text-xs text-muted">{{ cell.label }}</p>
            <p class="numeric mt-1 text-2xl font-semibold tracking-tight text-ink">{{ cell.value }}</p>
            <p v-if="cell.delta" class="mt-1 flex items-center gap-1 text-xs" :class="cell.positive ? 'text-primary' : 'text-danger'">
                <Icon :name="cell.positive ? 'up' : 'down'" :size="13" />
                <span class="numeric font-medium">{{ cell.delta }}</span>
                <span class="text-muted">{{ cell.compare }}</span>
            </p>
            <p v-else class="mt-1 text-xs text-muted">{{ cell.compare }}</p>
        </div>
    </div>
</template>
