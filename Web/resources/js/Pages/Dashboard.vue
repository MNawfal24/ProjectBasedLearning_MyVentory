<script setup>
import { Head, Link } from '@inertiajs/vue3';
import { computed } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { Button } from '@/Components/ui/button';
import AppLayout from '../Layouts/AppLayout.vue';
import BarChart from '../Components/BarChart.vue';
import Icon from '../Components/Icon.vue';
import Panel from '../Components/Panel.vue';
import PaymentMix from '../Components/PaymentMix.vue';
import RankList from '../Components/RankList.vue';
import RevenueChart from '../Components/RevenueChart.vue';
import StatStrip from '../Components/StatStrip.vue';
import { formatCurrency, formatDateTime, formatNumber } from '../format';
import { visitWith } from '../ui';

const props = defineProps({
    stats: { type: Object, required: true },
    filters: { type: Object, required: true },
    outlets: { type: Array, required: true },
    recent: { type: Array, required: true },
});

const periods = [
    { days: 7, label: '7 hari' },
    { days: 30, label: '30 hari' },
    { days: 90, label: '90 hari' },
    { days: 365, label: '1 tahun' },
];

const compareLabel = computed(() => `vs ${props.stats.period.days} hari sebelumnya`);

const kpis = computed(() => [
    {
        label: 'Penjualan bersih',
        value: formatCurrency(props.stats.kpis.revenue.value),
        change_pct: props.stats.kpis.revenue.change_pct,
        compare: compareLabel.value,
    },
    {
        label: 'Transaksi',
        value: formatNumber(props.stats.kpis.transactions.value),
        change_pct: props.stats.kpis.transactions.change_pct,
        compare: compareLabel.value,
    },
    {
        label: 'Rata-rata per struk',
        value: formatCurrency(props.stats.kpis.average_basket.value),
        change_pct: props.stats.kpis.average_basket.change_pct,
        compare: compareLabel.value,
    },
    {
        label: 'Item terjual',
        value: formatNumber(props.stats.kpis.items_sold.value),
        change_pct: props.stats.kpis.items_sold.change_pct,
        compare: compareLabel.value,
    },
]);

const hourItems = computed(() =>
    props.stats.hours.map((row) => ({ label: String(row.hour).padStart(2, '0'), value: row.transactions })),
);

const busiestHour = computed(() => {
    const rows = props.stats.hours.filter((row) => row.transactions > 0);

    return rows.length ? rows.reduce((best, row) => (row.transactions > best.transactions ? row : best)) : null;
});

const weekdayItems = computed(() => props.stats.weekdays.map((row) => ({ label: row.weekday, value: row.transactions })));

const topProducts = computed(() =>
    props.stats.top_products.map((row) => ({
        label: row.name,
        value: row.quantity,
        display: `${formatNumber(row.quantity)} pcs`,
    })),
);
</script>

<template>
    <Head title="Overview" />

    <AppLayout>
        <header class="flex flex-wrap items-end justify-between gap-4">
            <div>
                <h1 class="text-2xl font-semibold tracking-tight text-ink">Overview</h1>
                <p class="mt-1 text-sm text-muted">
                    Penjualan {{ stats.period.from }} sampai {{ stats.period.to }} · {{ stats.inventory.products }} produk aktif
                </p>
            </div>

            <div class="flex flex-wrap items-center gap-2">
                <div class="flex items-center gap-1" role="group" aria-label="Periode">
                    <Button
                        v-for="period in periods"
                        :key="period.days"
                        :variant="filters.days === period.days ? 'secondary' : 'ghost'"
                        size="sm"
                        :aria-pressed="filters.days === period.days"
                        @click="visitWith({ days: period.days })"
                    >
                        {{ period.label }}
                    </Button>
                </div>

                <label class="sr-only" for="outlet-filter">Outlet</label>
                <select
                    id="outlet-filter"
                    class="field w-auto"
                    :value="filters.outlet ?? ''"
                    @change="visitWith({ outlet: $event.target.value || null })"
                >
                    <option value="">Semua outlet</option>
                    <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                </select>
            </div>
        </header>

        <div class="mt-6">
            <StatStrip :items="kpis" />
        </div>

        <div class="mt-4 grid gap-4 lg:grid-cols-3 [&>*]:min-w-0">
            <div class="min-w-0 lg:col-span-2">
                <Panel
                    title="Tren penjualan harian"
                    :hint="`Garis putus-putus adalah rata-rata bergerak 7 hari, perataan yang memudarkan lonjakan akhir pekan.`"
                >
                    <RevenueChart :points="stats.daily" />
                </Panel>
            </div>

            <Panel title="Jam tersibuk" hint="Jumlah struk per jam pada periode ini.">
                <BarChart :items="hourItems" :height="168" />
                <p v-if="busiestHour" class="mt-3 text-xs text-muted">
                    Puncak pada {{ String(busiestHour.hour).padStart(2, '0') }}:00 dengan
                    {{ formatNumber(busiestHour.transactions) }} struk.
                </p>
            </Panel>
        </div>

        <div class="mt-4 grid gap-4 lg:grid-cols-3 [&>*]:min-w-0">
            <Panel title="Pola hari" hint="Total struk menurut hari dalam seminggu.">
                <BarChart :items="weekdayItems" :height="140" />
            </Panel>

            <Panel title="Metode pembayaran" hint="Porsi jumlah struk, bukan nilai rupiah.">
                <PaymentMix :items="stats.payments" />
            </Panel>

            <Panel title="Produk terlaris" hint="Delapan produk dengan unit terjual terbanyak.">
                <RankList :items="topProducts" />
            </Panel>
        </div>

        <div class="mt-4 grid gap-4 lg:grid-cols-3 [&>*]:min-w-0">
            <div class="min-w-0 lg:col-span-2">
                <Panel title="Transaksi terakhir" hint="Enam struk terbaru yang tercatat.">
                    <template #action>
                        <Link href="/transactions" class="text-xs font-medium text-primary hover:underline">
                            Lihat semua
                        </Link>
                    </template>

                    <ul v-if="recent.length" class="divide-y divide-dashed divide-line">
                        <!-- A table needs four columns to stay readable; on a phone the same
                             rows are stacked so nothing is clipped. -->
                        <li v-for="row in recent" :key="row.id" class="py-3 first:pt-0 last:pb-0">
                            <div class="flex items-baseline justify-between gap-3">
                                <span class="numeric text-xs text-muted">{{ row.receipt_number ?? `#${row.id}` }}</span>
                                <span class="numeric shrink-0 text-sm font-medium">{{ formatCurrency(row.total_amount) }}</span>
                            </div>
                            <p class="mt-0.5 text-xs text-muted">
                                {{ formatDateTime(row.occurred_at) }} · {{ row.outlet }}
                            </p>
                            <p class="mt-0.5 text-xs text-muted">
                                {{ row.items.map((item) => `${item.name} x${item.quantity}`).join(', ') }}
                            </p>
                        </li>
                    </ul>
                    <p v-else class="py-6 text-center text-sm text-muted">Belum ada transaksi.</p>
                </Panel>
            </div>

            <Panel title="Stok perlu perhatian" hint="Saldo pada atau di bawah batas minimum.">
                <template #action>
                    <Link href="/stock?status=low" class="text-xs font-medium text-primary hover:underline">
                        Kelola stok
                    </Link>
                </template>

                <ul v-if="stats.low_stock.length" class="divide-y divide-dashed divide-line">
                    <li
                        v-for="row in stats.low_stock"
                        :key="`${row.outlet}-${row.product}`"
                        class="flex items-start justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
                    >
                        <div class="min-w-0">
                            <p class="truncate text-sm text-ink">{{ row.product }}</p>
                            <p class="text-xs text-muted">{{ row.outlet }} · minimum {{ formatNumber(row.min_quantity) }} {{ row.unit }}</p>
                        </div>
                        <Badge variant="warning" class="numeric shrink-0 gap-1">
                            {{ formatNumber(row.quantity) }} {{ row.unit }}
                        </Badge>
                    </li>
                </ul>
                <p v-else class="flex items-center gap-2 py-6 text-sm text-muted">
                    <Icon name="check" :size="16" class="text-primary" />
                    Semua stok di atas batas minimum.
                </p>
            </Panel>
        </div>

        <div class="mt-4 grid gap-4 sm:grid-cols-3 [&>*]:min-w-0">
            <Panel title="Hari terakhir ada transaksi" :hint="stats.last_sale.date ?? 'Belum ada data'">
                <p class="numeric text-xl font-semibold text-ink">{{ formatCurrency(stats.last_sale.revenue) }}</p>
                <p class="mt-1 text-xs text-muted">{{ formatNumber(stats.last_sale.transactions) }} struk</p>
            </Panel>
            <Panel title="Unit di gudang" hint="Saldo seluruh outlet pada saat ini.">
                <p class="numeric text-xl font-semibold text-ink">{{ formatNumber(stats.inventory.units_on_hand) }}</p>
                <p class="mt-1 text-xs text-muted">{{ stats.inventory.products }} produk · {{ stats.inventory.outlets }} outlet</p>
            </Panel>
            <Panel title="Rata-rata item per struk" hint="Total item dibagi jumlah struk pada periode.">
                <p class="numeric text-xl font-semibold text-ink">
                    {{
                        stats.kpis.transactions.value
                            ? (stats.kpis.items_sold.value / stats.kpis.transactions.value).toFixed(2).replace('.', ',')
                            : '0,00'
                    }}
                </p>
                <p class="mt-1 text-xs text-muted">Item terjual {{ formatNumber(stats.kpis.items_sold.value) }}</p>
            </Panel>
        </div>
    </AppLayout>
</template>
