<script setup>
import { Head } from '@inertiajs/vue3';
import { computed } from 'vue';
import AppLayout from '../../Layouts/AppLayout.vue';
import PageHeader from '../../Components/PageHeader.vue';
import Panel from '../../Components/Panel.vue';
import { VChart } from '../../echarts';
import { formatCompact, formatCurrency } from '../../format';
import { useChartColors, useTheme } from '../../ui';

const props = defineProps({
    segmentation: { type: Object, default: null },
});

const colors = useChartColors();
const { isDark } = useTheme();

const segmentOrder = ['Best Seller', 'Regular Seller', 'Seasonal Product', 'Slow Moving'];
const segments = computed(() => Object.entries(props.segmentation?.top_products ?? {}));

function withAlpha(hex, alpha) {
    const value = hex.trim().replace('#', '');
    const full = value.length === 3 ? value.split('').map((char) => char + char).join('') : value;
    const [r, g, b] = [0, 2, 4].map((offset) => parseInt(full.slice(offset, offset + 2), 16));
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const rankColors = computed(() => [1, 0.82, 0.64, 0.46, 0.3].map((alpha) => withAlpha(colors.value.primary, alpha)));

const rankSeries = computed(() => [0, 1, 2, 3, 4].map((index) => ({
    name: `Top ${index + 1}`,
    color: rankColors.value[index],
    items: segmentOrder.map((segment) => props.segmentation?.top_products?.[segment]?.[index] ?? null),
})));

const chartOption = computed(() => ({
    tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: isDark.value ? 'rgba(134,161,255,0.12)' : 'rgba(31,77,255,0.08)' } },
        backgroundColor: isDark.value ? '#20315f' : '#0f1b3d',
        borderWidth: 0,
        padding: [10, 12],
        textStyle: { color: '#ffffff', fontSize: 12 },
        extraCssText: 'border-radius:12px;',
        formatter: (params) => {
            const segment = params[0]?.axisValue ?? '';
            const rows = params
                .filter((param) => param.value != null)
                .map((param) => {
                    const item = rankSeries.value.find((series) => series.name === param.seriesName)?.items[param.dataIndex];
                    const dot = `<span style="display:inline-block;width:8px;height:8px;border-radius:3px;background:${param.color};margin-right:6px"></span>`;
                    return `<div style="margin-top:4px;font-size:12px">${dot}${item?.product ?? param.seriesName} &middot; <b>${formatCurrency(param.value)}</b></div>`;
                })
                .join('');
            return `<div style="font-size:11px;color:#a7b2c6">${segment}</div>${rows}`;
        },
    },
    legend: {
        top: 0,
        left: 0,
        itemGap: 18,
        itemWidth: 10,
        itemHeight: 10,
        icon: 'roundRect',
        textStyle: { color: colors.value.muted, fontSize: 11 },
    },
    grid: { left: 4, right: 8, top: 44, bottom: 4, containLabel: true },
    xAxis: {
        type: 'category',
        data: segmentOrder,
        axisTick: { show: false },
        axisLine: { show: false },
        axisLabel: { color: colors.value.muted, fontSize: 11, interval: 0, margin: 12 },
    },
    yAxis: {
        type: 'value',
        splitNumber: 4,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: colors.value.muted, fontSize: 11, formatter: (value) => formatCompact(value) },
        splitLine: { lineStyle: { color: colors.value.line, type: 'dashed' } },
    },
    series: rankSeries.value.map((series) => ({
        name: series.name,
        type: 'bar',
        barMaxWidth: 16,
        barGap: '12%',
        barCategoryGap: '40%',
        itemStyle: { color: series.color, borderRadius: [8, 8, 0, 0] },
        data: series.items.map((item) => item?.revenue ?? null),
    })),
}));

function errorOf(result) {
    return result?.error ?? null;
}
</script>

<template>
    <Head title="Prediksi" />
    <AppLayout>
        <PageHeader title="Segmentasi Produk" description="Lima produk teratas pada setiap segmen hasil model ML." />

        <div class="mt-8">
                <Panel title="Segmentasi produk" hint="Top 5 produk pada setiap segmen hasil model ML.">
                <p v-if="errorOf(segmentation)" class="py-10 text-center text-body text-danger">{{ errorOf(segmentation) }}</p>
                <template v-else-if="segmentation">
                    <VChart v-if="segments.length" :option="chartOption" autoresize style="height: 320px" role="img" aria-label="Top 5 produk pada setiap segmen" />
                    <p v-else class="py-10 text-center text-body text-muted">Belum ada hasil segmentasi.</p>
                </template>
                <p v-else class="py-10 text-center text-body text-muted">Belum ada data produk untuk disegmentasikan.</p>
            </Panel>
        </div>
    </AppLayout>
</template>
