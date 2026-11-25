<script setup>
import { graphic } from 'echarts/core';
import { computed } from 'vue';
import { VChart } from '../echarts';
import { formatCompact, formatDate, formatNumber, formatShortDate } from '../format';
import { useChartColors, useTheme } from '../ui';

const props = defineProps({
    forecast: { type: Object, required: true },
    height: { type: Number, default: 300 },
});

const colors = useChartColors();
const { isDark } = useTheme();

const history = computed(() => props.forecast?.recent_history ?? []);
const predicted = computed(() => props.forecast?.predictions ?? []);
const chartPoints = computed(() => [...history.value, ...predicted.value]);
const labelInterval = computed(() => Math.max(0, Math.ceil(chartPoints.value.length / 5) - 1));
const summary = computed(
    () => `Permintaan harian dengan ${history.value.length} hari aktual dan ${predicted.value.length} hari prediksi.`,
);

function withAlpha(hex, alpha) {
    const value = hex.replace('#', '');
    if (value.length !== 6) return hex;
    return `rgba(${parseInt(value.slice(0, 2), 16)}, ${parseInt(value.slice(2, 4), 16)}, ${parseInt(value.slice(4, 6), 16)}, ${alpha})`;
}

const actualGradient = computed(
    () => new graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: withAlpha(colors.value.primary, 0.18) },
        { offset: 1, color: withAlpha(colors.value.primary, 0) },
    ]),
);

const predictionGradient = computed(
    () => new graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: withAlpha(colors.value.muted, 0.18) },
        { offset: 1, color: withAlpha(colors.value.muted, 0) },
    ]),
);

function tooltip(params) {
    const point = chartPoints.value[params[0].dataIndex];
    const rows = params.filter((item) => item.value !== undefined && item.value !== null);
    const primary = rows.find((item) => item.seriesName === 'Aktual') ?? rows[0];
    const label = isDark.value ? '#9aa7c2' : '#a7b2c6';

    return `
        <p style="font-size:10px;letter-spacing:0.08em;text-transform:uppercase;color:${label}">${primary.seriesName}</p>
        <p style="margin-top:4px;font-size:17px;font-weight:600;color:#ffffff">${formatNumber(primary.value)} unit</p>
        <p style="margin-top:2px;font-size:11px;color:${label}">${formatDate(point.date)}</p>
    `;
}

const option = computed(() => ({
    animationDuration: 400,
    grid: { left: 0, right: 8, top: 20, bottom: 0, containLabel: true },
    tooltip: {
        trigger: 'axis',
        backgroundColor: isDark.value ? '#20315f' : '#0f1b3d',
        borderWidth: 0,
        padding: [10, 14],
        textStyle: { color: '#ffffff', fontSize: 12 },
        extraCssText: 'border-radius:10px;box-shadow:0 12px 28px -18px rgba(15,27,61,0.7);',
        axisPointer: { type: 'line', lineStyle: { color: colors.value.primary, width: 1 }, label: { show: false } },
        formatter: tooltip,
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: chartPoints.value.map((point) => point.date),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
            color: colors.value.muted,
            fontSize: 11,
            margin: 14,
            interval: labelInterval.value,
            formatter: (value) => formatShortDate(value).replace(/^0/, ''),
        },
        splitLine: { show: false },
    },
    yAxis: {
        type: 'value',
        min: 0,
        splitNumber: 4,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: colors.value.muted, fontSize: 10, margin: 10, formatter: (value) => formatCompact(value) },
        splitLine: { lineStyle: { color: colors.value.line, type: [4, 4] } },
    },
    series: [
        {
            name: 'Aktual',
            type: 'line',
            smooth: 0.35,
            showSymbol: false,
            data: [...history.value.map((point) => point.qty), ...predicted.value.map(() => null)],
            lineStyle: { width: 2.5, color: colors.value.primary },
            itemStyle: { color: colors.value.primary, borderColor: colors.value.surface, borderWidth: 2 },
            areaStyle: { color: actualGradient.value },
            emphasis: { scale: 1.4 },
        },
        {
            name: 'Prediksi',
            type: 'line',
            smooth: 0.35,
            showSymbol: false,
            data: [
                ...history.value.map((point, index) => (index === history.value.length - 1 ? point.qty : null)),
                ...predicted.value.map((point) => point.predicted_qty),
            ],
            lineStyle: { width: 1.5, type: [2, 4], color: colors.value.muted, opacity: 0.85 },
            itemStyle: { color: colors.value.muted, borderColor: colors.value.surface, borderWidth: 2 },
            areaStyle: { color: predictionGradient.value },
            emphasis: { scale: 1.4 },
        },
    ],
}));
</script>

<template>
    <div>
        <div v-if="!chartPoints.length" class="flex items-center justify-center text-body text-muted" :style="{ height: `${height}px` }">
            Belum ada data permintaan.
        </div>
        <VChart v-else :option="option" autoresize :style="{ height: `${height}px` }" role="img" :aria-label="summary" />
    </div>
</template>
