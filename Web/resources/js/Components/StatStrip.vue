<script setup>
import { computed } from 'vue';
import Icon from './Icon.vue';

const props = defineProps({
    items: { type: Array, required: true },
});

/*
 * The strip is read as one instrument, so each cell carries the same three parts:
 * label, figure, and the comparison the figure was measured against. The caption
 * is derived by the page, so it stays true when the period or the data changes.
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
    <div class="strip grid-cols-2 lg:grid-cols-4">
        <div v-for="cell in cells" :key="cell.label" class="strip-cell">
            <p class="strip-label">{{ cell.label }}</p>
            <p class="strip-value">{{ cell.value }}</p>
            <p v-if="cell.delta || cell.compare" class="flex flex-wrap items-center gap-1.5 text-2xs text-muted">
                <span
                    v-if="cell.delta"
                    class="numeric inline-flex items-center gap-0.5 font-medium"
                    :class="cell.positive ? 'text-primary' : 'text-danger'"
                >
                    <Icon :name="cell.positive ? 'up' : 'down'" :size="12" />
                    {{ cell.delta }}
                </span>
                <span v-if="cell.compare">{{ cell.compare }}</span>
            </p>
        </div>
    </div>
</template>