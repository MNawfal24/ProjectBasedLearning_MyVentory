<script setup>
import { computed } from 'vue';
import { VChart } from '../echarts';
import { formatCompact, formatNumber } from '../format';
import { useChartColors } from '../ui';

const props = defineProps({
    categories: { type: Array, required: true },
    series: { type: Array, required: true },
    stack: { type: Boolean, default: false },
    horizontal: { type: Boolean, default: false },
    height: { type: Number, default: 240 },
    suffix: { type: String, default: '' },
});

const colors = useChartColors();

const labels = computed(() => (props.horizontal ? [...props.categories].reverse() : props.categories));

const data = computed(() =>
    props.series.map((serie, index) => {
        const values = props.horizontal ? [...serie.data].reverse() : serie.data;
        const start = index === 0;
        const end = index === props.series.length - 1;
        const radius = props.horizontal
            ? [start ? 6 : 0, end ? 6 : 0, end ? 6 : 0, start ? 6 : 0]
            : [end ? 6 : 0, end ? 6 : 0, start ? 6 : 0, start ? 6 : 0];

        return {
            name: serie.name,
            type: 'bar',
            stack: props.stack ? 'total' : undefined,
            barMaxWidth: props.horizontal ? 18 : 30,
            itemStyle: { color: serie.color, borderRadius: radius },
            data: values,
        };
    }),
);

const option = computed(() => ({
    animationDuration: 400,
    grid: { left: 0, right: 8, top: 8, bottom: 0, containLabel: true },
    tooltip: {
        trigger: 'axis',
        backgroundColor: colors.value.surface,
        borderColor: colors.value.line,
        textStyle: { color: colors.value.ink, fontSize: 12 },
        axisPointer: { type: 'shadow' },
        valueFormatter: (value) => `${formatNumber(value)}${props.suffix}`,
    },
    xAxis: props.horizontal
        ? {
              type: 'value',
              splitLine: { lineStyle: { color: colors.value.line, type: 'dashed' } },
              axisLabel: { color: colors.value.muted, fontSize: 11, formatter: (value) => formatCompact(value) },
          }
        : {
              type: 'category',
              data: labels.value,
              axisLine: { lineStyle: { color: colors.value.line } },
              axisTick: { show: false },
              axisLabel: { color: colors.value.muted, fontSize: 11 },
          },
    yAxis: props.horizontal
        ? {
              type: 'category',
              data: labels.value,
              axisLine: { lineStyle: { color: colors.value.line } },
              axisTick: { show: false },
              axisLabel: { color: colors.value.muted, fontSize: 11, width: 150, overflow: 'truncate' },
          }
        : {
              type: 'value',
              splitLine: { lineStyle: { color: colors.value.line, type: 'dashed' } },
              axisLabel: { color: colors.value.muted, fontSize: 11, formatter: (value) => formatCompact(value) },
          },
    series: data.value,
}));
</script>

<template>
    <div v-if="categories.length === 0" class="flex items-center justify-center text-sm text-muted" :style="{ height: `${height}px` }">
        Belum ada data.
    </div>
    <VChart v-else :option="option" autoresize :style="{ height: `${height}px` }" />
</template>
