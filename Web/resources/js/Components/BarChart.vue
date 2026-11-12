<script setup>
import { computed } from 'vue';
import { VChart } from '../echarts';
import { formatNumber } from '../format';
import { useChartColors, useTheme } from '../ui';

const props = defineProps({
    items: { type: Array, required: true },
    height: { type: Number, default: 200 },
});

const colors = useChartColors();
const { isDark } = useTheme();

const option = computed(() => ({
    animationDuration: 400,
    grid: { left: 0, right: 4, top: 12, bottom: 0, containLabel: true },
    tooltip: {
        trigger: 'axis',
        backgroundColor: isDark.value ? '#20315f' : '#0f1b3d',
        borderWidth: 0,
        padding: [8, 12],
        textStyle: { color: '#ffffff', fontSize: 12 },
        extraCssText: 'border-radius:10px;',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(31,77,255,0.08)' } },
        formatter: (params) => {
            const item = params[0];
            return `<p style="font-size:11px;color:#a7b2c6">${item.name}</p><p style="margin-top:2px;font-size:13px;font-weight:600;color:#ffffff">${formatNumber(item.value)}</p>`;
        },
    },
    xAxis: {
        type: 'category',
        data: props.items.map((item) => item.label),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
            color: colors.value.muted,
            fontSize: 11,
            interval: props.items.length > 12 ? 2 : 0,
        },
        splitLine: { show: true, lineStyle: { color: colors.value.line, type: 'dashed' } },
    },
    yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false },
    },
    series: [
        {
            type: 'bar',
            data: props.items.map((item) => item.value),
            barMaxWidth: 18,
            itemStyle: { color: colors.value.primary, borderRadius: [6, 6, 0, 0] },
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
