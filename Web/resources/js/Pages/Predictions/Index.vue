<script setup>
import { Head } from '@inertiajs/vue3';
import { computed } from 'vue';
import AppLayout from '../../Layouts/AppLayout.vue';
import DemandForecastChart from '../../Components/DemandForecastChart.vue';
import PageHeader from '../../Components/PageHeader.vue';
import Panel from '../../Components/Panel.vue';
import { VChart } from '../../echarts';
import { formatCompact, formatCurrency, formatDate, formatNumber } from '../../format';
import { useChartColors, useTheme, visitWith } from '../../ui';

const props = defineProps({
    products: { type: Array, default: () => [] },
    demand_filters: { type: Object, required: true },
    demand: { type: Object, default: null },
    segmentation: { type: Object, default: null },
});

const colors = useChartColors();
const { isDark } = useTheme();

const demandError = computed(() => props.demand?.error ?? null);
const demandMeta = computed(() => {
    if (!props.demand || demandError.value) return '';

    const parts = [];
    if (props.demand.history_end) parts.push(`Histori s.d. ${formatDate(props.demand.history_end)}`);
    if (props.demand.model_version) parts.push(`Model v${props.demand.model_version}`);

    return parts.join(' · ');
});

const demandStats = computed(() => {
    const summary = props.demand?.summary;
    if (!summary) return [];

    return [
        { label: 'Total permintaan', value: formatNumber(summary.total_predicted_qty), unit: 'unit' },
        { label: 'Rata-rata harian', value: formatNumber(summary.average_daily_qty), unit: 'unit/hari' },
        { label: 'Saran pesan ulang', value: formatNumber(summary.suggested_reorder_qty), unit: 'unit / 7 hari' },
        { label: 'Aktual 7 hari', value: formatNumber(summary.last_7_days_actual_qty), unit: 'unit' },
    ];
});

const horizonOptions = computed(() => [...new Set([3, 7, 14, Number(props.demand_filters.horizon_days)])].sort((a, b) => a - b));

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
        <PageHeader title="Prediksi" description="Prediksi permintaan produk dan segmentasi dari model ML terbaru." />

        <div class="mt-8 space-y-4">
            <Panel title="Prediksi permintaan produk" hint="Permintaan harian per produk: 7 hari aktual terakhir dan horizon prediksi.">
                <template #action>
                    <div class="flex flex-wrap items-end gap-2">
                        <div class="min-w-0">
                            <label for="demand-product" class="sr-only">Produk</label>
                            <select
                                id="demand-product"
                                class="field h-9 w-full max-w-72 text-xs sm:w-auto"
                                :value="demand_filters.product ?? ''"
                                @change="visitWith({ product: $event.target.value || null })"
                            >
                                <option v-for="product in products" :key="product" :value="product">{{ product }}</option>
                            </select>
                        </div>
                        <div>
                            <label for="demand-horizon" class="sr-only">Horizon prediksi</label>
                            <select
                                id="demand-horizon"
                                class="field h-9 w-auto text-xs"
                                :value="demand_filters.horizon_days"
                                @change="visitWith({ horizon_days: $event.target.value })"
                            >
                                <option v-for="horizon in horizonOptions" :key="horizon" :value="horizon">{{ horizon }} hari</option>
                            </select>
                        </div>
                    </div>
                </template>

                <p v-if="demandError" class="py-10 text-center text-body text-danger">{{ demandError }}</p>
                <template v-else-if="demand?.summary">
                    <div class="strip sm:grid-cols-2 xl:grid-cols-4">
                        <div v-for="stat in demandStats" :key="stat.label" class="strip-cell">
                            <span class="strip-label">{{ stat.label }}</span>
                            <span class="strip-value">{{ stat.value }}</span>
                            <span class="text-2xs text-muted">{{ stat.unit }}</span>
                        </div>
                    </div>

                    <p v-if="demandMeta" class="mt-4 text-2xs text-muted">{{ demandMeta }}</p>
                    <DemandForecastChart :forecast="demand" :height="320" />
                    <p v-if="demand.note" class="mt-2 text-2xs text-muted">{{ demand.note }}</p>
                </template>
                <p v-else class="py-10 text-center text-body text-muted">Belum ada hasil prediksi permintaan.</p>
            </Panel>

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
