<script setup>
import { computed } from 'vue';
import { VChart } from '../echarts';
import { formatCompact } from '../format';
import { useChartColors } from '../ui';

const props = defineProps({
    items: { type: Array, required: true },
    height: { type: Number, default: 150 },
});

const colors = useChartColors();

const option = computed(() => ({
    animationDuration: 400,
    grid: { left: 0, right: 4, top: 12, bottom: 0, containLabel: true },
    tooltip: {
        trigger: 'axis',
        backgroundColor: colors.value.surface,
        borderColor: colors.value.line,
        textStyle: { color: colors.value.ink, fontSize: 12 },
        axisPointer: { type: 'shadow' },
        valueFormatter: (value) => formatCompact(value),
    },
    xAxis: {
        type: 'category',
        data: props.items.map((item) => item.label),
        axisLine: { lineStyle: { color: colors.value.line } },
        axisTick: { show: false },
        axisLabel: {
            color: colors.value.muted,
            fontSize: 11,
            interval: props.items.length > 12 ? 2 : 0,
        },
    },
    yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: colors.value.line, type: 'dashed' } },
        axisLabel: { color: colors.value.muted, fontSize: 11, formatter: (value) => formatCompact(value) },
    },
    series: [
        {
            type: 'bar',
            data: props.items.map((item) => item.value),
            barMaxWidth: 18,
            itemStyle: { color: colors.value.primary, borderRadius: [4, 4, 0, 0] },
        },
    ],
}));
</script>

<template>
    <div v-if="items.length === 0" class="flex items-center justify-center text-sm text-muted" :style="{ height: `${height}px` }">
        Belum ada data.
    </div>
    <VChart v-else :option="option" autoresize :style="{ height: `${height}px` }" />
</template>
