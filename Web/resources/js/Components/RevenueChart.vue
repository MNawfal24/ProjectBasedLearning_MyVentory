<script setup>
import { computed } from 'vue';
import { VChart } from '../echarts';
import { formatCompact, formatCurrency, formatDate } from '../format';
import { useChartColors } from '../ui';

const props = defineProps({
    points: { type: Array, required: true },
    height: { type: Number, default: 280 },
});

const colors = useChartColors();

const summary = computed(() => {
    const total = props.points.reduce((sum, point) => sum + point.revenue, 0);
    const average = props.points.length ? total / props.points.length : 0;

    return `Tren penjualan harian, ${props.points.length} hari, total ${formatCurrency(total)}, rata-rata ${formatCurrency(average)} per hari.`;
});

function tooltip(params) {
    const point = props.points[params[0].dataIndex];
    const muted = colors.value.muted;
    const ink = colors.value.ink;

    return [
        `<p style="font-size:11px;color:${muted}">${formatDate(point.date)}</p>`,
        `<p style="font-size:12px;font-weight:500;color:${ink}">${formatCurrency(point.revenue)}</p>`,
        `<p style="font-size:11px;color:${muted}">Rata-rata 7 hari ${formatCurrency(point.moving_average)}</p>`,
    ].join('');
}

const option = computed(() => ({
    animationDuration: 400,
    grid: { left: 0, right: 8, top: 12, bottom: 0, containLabel: true },
    tooltip: {
        trigger: 'axis',
        backgroundColor: colors.value.surface,
        borderColor: colors.value.line,
        padding: [8, 12],
        textStyle: { color: colors.value.ink, fontSize: 12 },
        formatter: tooltip,
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: props.points.map((point) => formatDate(point.date)),
        axisLine: { lineStyle: { color: colors.value.line } },
        axisTick: { show: false },
        axisLabel: { color: colors.value.muted, fontSize: 11, hideOverlap: true },
    },
    yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: colors.value.line, type: 'dashed' } },
        axisLabel: { color: colors.value.muted, fontSize: 11, formatter: (value) => formatCompact(value) },
    },
    series: [
        {
            name: 'Penjualan harian',
            type: 'line',
            showSymbol: false,
            data: props.points.map((point) => point.revenue),
            lineStyle: { width: 2.2, color: colors.value.primary },
            itemStyle: { color: colors.value.primary },
            areaStyle: { color: colors.value.primary, opacity: 0.1 },
        },
        {
            name: 'Rata-rata bergerak 7 hari',
            type: 'line',
            showSymbol: false,
            data: props.points.map((point) => point.moving_average),
            lineStyle: { width: 1.5, type: 'dashed', color: colors.value.muted },
            itemStyle: { color: colors.value.muted },
        },
    ],
}));
</script>

<template>
    <div>
        <div
            v-if="points.length === 0"
            class="flex items-center justify-center text-body text-muted"
            :style="{ height: `${height}px` }"
        >
            Belum ada transaksi pada periode ini.
        </div>

        <template v-else>
            <div class="mb-3 flex flex-wrap items-center gap-4 text-xs text-muted">
                <span class="flex items-center gap-2">
                    <span class="h-0.5 w-4 rounded-full" :style="{ backgroundColor: colors.primary }"></span> Penjualan harian
                </span>
                <span class="flex items-center gap-2">
                    <span class="h-0.5 w-4 rounded-full border-t border-dashed border-muted"></span> Rata-rata bergerak 7 hari
                </span>
            </div>

            <VChart
                :option="option"
                autoresize
                :style="{ height: `${height}px` }"
                role="img"
                :aria-label="summary"
            />
        </template>
    </div>
</template>