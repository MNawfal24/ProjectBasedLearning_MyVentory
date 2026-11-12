<script setup>
import { computed } from 'vue';
import Icon from './Icon.vue';

const props = defineProps({
    items: { type: Array, required: true },
});

/*
 * Each KPI is a card with one icon tile, the figure and the comparison it was
 * measured against. The caption is derived by the page, so it stays true when
 * the period or the data changes.
 */
const cells = computed(() =>
    props.items.map((item) => {
        const change = item.change_pct;
        const positive = change !== null && change !== undefined && change >= 0;

        return {
            ...item,
            positive,
            delta:
                change === null || change === undefined
                    ? null
                    : `${positive ? '+' : ''}${String(change).replace('.', ',')}%`,
        };
    }),
);
</script>

<template>
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article v-for="cell in cells" :key="cell.label" class="panel p-5">
            <div class="flex items-start justify-between gap-3">
                <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
                    <Icon :name="cell.icon ?? 'overview'" :size="20" />
                </span>
                <span
                    v-if="cell.delta"
                    class="numeric inline-flex items-center gap-0.5 rounded-md px-1.5 py-1 text-2xs font-medium"
                    :class="cell.positive ? 'bg-primary-soft text-primary' : 'bg-danger-soft text-danger'"
                >
                    <Icon :name="cell.positive ? 'up' : 'down'" :size="12" />
                    {{ cell.delta }}
                </span>
            </div>
            <p class="mt-4 text-2xs font-medium text-muted">{{ cell.label }}</p>
            <p class="numeric mt-1 text-metric font-semibold tracking-tight text-ink">{{ cell.value }}</p>
            <p v-if="cell.compare" class="mt-1 text-2xs text-muted">{{ cell.compare }}</p>
        </article>
    </div>
</template>
