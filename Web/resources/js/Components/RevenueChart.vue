<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { formatCompact, formatCurrency, formatDate, formatShortDate } from '../format';

const props = defineProps({
    points: { type: Array, required: true },
});

// The viewBox follows the container width so labels keep their real pixel size.
// A fixed 900-unit viewBox squeezed onto a phone would render 11px text at ~4px.
const container = ref(null);
const width = ref(900);
const height = computed(() => (width.value < 560 ? 220 : 300));
const PAD = { top: 16, right: 44, bottom: 28, left: 56 };
const innerWidth = computed(() => width.value - PAD.left - PAD.right);
const innerHeight = computed(() => height.value - PAD.top - PAD.bottom);

const hovered = ref(null);

function measure() {
    const element = container.value;
    if (element) {
        width.value = Math.max(280, Math.round(element.clientWidth));
    }
}

// Measured after paint and on resize. ResizeObserver was unreliable here: on a
// phone viewport it could stay silent and leave the 900-unit fallback in place.
let frame = null;

function scheduleMeasure() {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(measure);
}

onMounted(() => {
    scheduleMeasure();
    window.addEventListener('resize', scheduleMeasure);
});

onBeforeUnmount(() => {
    cancelAnimationFrame(frame);
    window.removeEventListener('resize', scheduleMeasure);
});

const max = computed(() => Math.max(1, ...props.points.map((point) => point.revenue)));
const lastIndex = computed(() => Math.max(0, props.points.length - 1));

function x(index) {
    return props.points.length === 1
        ? PAD.left + innerWidth.value / 2
        : PAD.left + (index / lastIndex.value) * innerWidth.value;
}

function y(value) {
    return PAD.top + innerHeight.value - (value / max.value) * innerHeight.value;
}

const linePath = computed(() =>
    props.points.map((point, index) => `${index === 0 ? 'M' : 'L'}${x(index).toFixed(2)},${y(point.revenue).toFixed(2)}`).join(' '),
);

const areaPath = computed(() => {
    if (props.points.length === 0) {
        return '';
    }

    return `${linePath.value} L${x(lastIndex.value).toFixed(2)},${PAD.top + innerHeight.value} L${x(0).toFixed(2)},${PAD.top + innerHeight.value} Z`;
});

const averagePath = computed(() =>
    props.points
        .map((point, index) => `${index === 0 ? 'M' : 'L'}${x(index).toFixed(2)},${y(point.moving_average).toFixed(2)}`)
        .join(' '),
);

const gridLines = computed(() =>
    [0, 0.25, 0.5, 0.75, 1].map((fraction) => ({
        value: max.value * fraction,
        y: y(max.value * fraction),
    })),
);

/**
 * Date labels are placed only where they fit. Each candidate is measured against
 * the previous label's right edge using the anchor it will actually use, so the
 * first (start-anchored) and last (end-anchored) ticks never collide.
 */
const xLabels = computed(() => {
    const narrow = width.value < 560;
    const total = props.points.length;
    if (total === 0) {
        return [];
    }

    const step = Math.max(1, Math.ceil(total / (narrow ? 3 : 7)));
    const indices = [...new Set([...Array(total).keys()].filter((index) => index % step === 0).concat(total - 1))];
    const placed = [];
    let occupiedRight = -Infinity;

    for (const index of indices) {
        const anchor = index === 0 ? 'start' : index === total - 1 ? 'end' : 'middle';
        const label = narrow ? formatShortDate(props.points[index].date) : formatDate(props.points[index].date);
        const estimatedWidth = label.length * 6.6;
        const center = x(index);
        const left = anchor === 'start' ? center : anchor === 'end' ? center - estimatedWidth : center - estimatedWidth / 2;
        const right = anchor === 'start' ? center + estimatedWidth : anchor === 'end' ? center : center + estimatedWidth / 2;

        if (left < occupiedRight + 10) {
            continue;
        }
        occupiedRight = right;
        placed.push({ index, label, anchor });
    }

    return placed;
});

const active = computed(() => (hovered.value === null ? null : props.points[hovered.value]));

function onPointerMove(event) {
    if (props.points.length === 0) {
        return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    const px = ((event.clientX - rect.left) / rect.width) * width.value;
    const ratio = (px - PAD.left) / innerWidth.value;
    hovered.value = Math.min(lastIndex.value, Math.max(0, Math.round(ratio * lastIndex.value)));
}

const tooltipStyle = computed(() => {
    if (!active.value) {
        return {};
    }
    const left = Math.min(88, Math.max(12, (x(hovered.value) / width.value) * 100));

    return { left: `${left}%`, top: `${(y(active.value.revenue) / height.value) * 100}%` };
});

const summary = computed(() => {
    const total = props.points.reduce((sum, point) => sum + point.revenue, 0);
    const average = props.points.length ? total / props.points.length : 0;

    return `Tren penjualan harian, ${props.points.length} hari, total ${formatCurrency(total)}, rata-rata ${formatCurrency(average)} per hari.`;
});
</script>

<template>
    <div ref="container" class="relative">
        <div v-if="points.length === 0" class="flex h-56 items-center justify-center text-sm text-muted">
            Belum ada transaksi pada periode ini.
        </div>

        <template v-else>
            <div class="mb-3 flex flex-wrap items-center gap-4 text-xs text-muted">
                <span class="flex items-center gap-2">
                    <span class="h-0.5 w-4 rounded-full bg-primary"></span> Penjualan harian
                </span>
                <span class="flex items-center gap-2">
                    <span class="h-0.5 w-4 rounded-full border-t border-dashed border-muted"></span> Rata-rata bergerak 7 hari
                </span>
            </div>

            <svg
                :viewBox="`0 0 ${width} ${height}`"
                :style="{ height: `${height}px` }"
                class="w-full"
                role="img"
                :aria-label="summary"
                @pointermove="onPointerMove"
                @pointerleave="hovered = null"
            >
                <g>
                    <line
                        v-for="line in gridLines"
                        :key="line.value"
                        :x1="PAD.left"
                        :x2="width - PAD.right"
                        :y1="line.y"
                        :y2="line.y"
                        stroke="var(--color-line)"
                        stroke-width="1"
                    />
                    <text
                        v-for="line in gridLines"
                        :key="`label-${line.value}`"
                        :x="PAD.left - 10"
                        :y="line.y + 4"
                        text-anchor="end"
                        class="numeric"
                        fill="var(--color-muted)"
                        font-size="11"
                    >
                        {{ formatCompact(line.value) }}
                    </text>
                </g>

                <path :d="areaPath" fill="var(--color-primary)" fill-opacity="0.10" />
                <path :d="averagePath" fill="none" stroke="var(--color-muted)" stroke-width="1.5" stroke-dasharray="5 5" />
                <path :d="linePath" fill="none" stroke="var(--color-primary)" stroke-width="2.2" stroke-linejoin="round" />

                <g v-if="hovered !== null">
                    <line
                        :x1="x(hovered)"
                        :x2="x(hovered)"
                        :y1="PAD.top"
                        :y2="PAD.top + innerHeight"
                        stroke="var(--color-primary)"
                        stroke-width="1"
                        stroke-dasharray="3 3"
                    />
                    <circle :cx="x(hovered)" :cy="y(points[hovered].revenue)" r="4" fill="var(--color-primary)" />
                </g>

                <text
                    v-for="label in xLabels"
                    :key="label.index"
                    :x="x(label.index)"
                    :y="height - 8"
                    :text-anchor="label.anchor"
                    fill="var(--color-muted)"
                    font-size="11"
                >
                    {{ label.label }}
                </text>
            </svg>

            <div
                v-if="active"
                class="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-sm"
                :style="tooltipStyle"
            >
                <p class="font-medium text-ink">{{ formatDate(active.date) }}</p>
                <p class="numeric mt-1 text-muted">{{ formatCurrency(active.revenue) }}</p>
                <p class="numeric text-muted">Rata-rata 7 hari {{ formatCurrency(active.moving_average) }}</p>
            </div>
        </template>
    </div>
</template>
