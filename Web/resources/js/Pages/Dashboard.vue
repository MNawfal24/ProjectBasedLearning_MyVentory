<script setup>
import { Head, Link } from '@inertiajs/vue3';
import { computed } from 'vue';
import { Badge } from '@/Components/ui/badge';
import AppLayout from '../Layouts/AppLayout.vue';
import BarChart from '../Components/BarChart.vue';
import Icon from '../Components/Icon.vue';
import PageHeader from '../Components/PageHeader.vue';
import Panel from '../Components/Panel.vue';
import PaymentMix from '../Components/PaymentMix.vue';
import RankList from '../Components/RankList.vue';
import RevenueChart from '../Components/RevenueChart.vue';
import StatStrip from '../Components/StatStrip.vue';
import { formatCurrency, formatDate, formatDateTime, formatNumber } from '../format';
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

const range = computed(() => `${formatDate(props.stats.period.from)} sampai ${formatDate(props.stats.period.to)}`);

// Lengkapnya periode, bukan tanggal: angkanya tetap terbaca saat data bergeser.
const compareLabel = computed(() => `vs ${props.stats.period.days} hari sebelumnya`);

const compare = (changePct) => (changePct === null ? '' : compareLabel.value);

const kpis = computed(() => [
    {
        label: 'Penjualan bersih',
        value: formatCurrency(props.stats.kpis.revenue.value),
        change_pct: props.stats.kpis.revenue.change_pct,
        compare: compare(props.stats.kpis.revenue.change_pct),
    },
    {
        label: 'Transaksi',
        value: formatNumber(props.stats.kpis.transactions.value),
        change_pct: props.stats.kpis.transactions.change_pct,
        compare: compare(props.stats.kpis.transactions.change_pct),
    },
    {
        label: 'Rata-rata per struk',
        value: formatCurrency(props.stats.kpis.average_basket.value),
        change_pct: props.stats.kpis.average_basket.change_pct,
        compare: compare(props.stats.kpis.average_basket.change_pct),
    },
    {
        label: 'Item terjual',
        value: formatNumber(props.stats.kpis.items_sold.value),
        change_pct: props.stats.kpis.items_sold.change_pct,
        compare: compare(props.stats.kpis.items_sold.change_pct),
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

const itemsPerReceipt = computed(() =>
    props.stats.kpis.transactions.value
        ? (props.stats.kpis.items_sold.value / props.stats.kpis.transactions.value).toFixed(2).replace('.', ',')
        : '0,00',
);
</script>

<template>
    <Head title="Overview" />

    <AppLayout>
        <PageHeader
            title="Overview"
            :description="`Penjualan ${range}`"
            :meta="
                stats.data_range.from
                    ? `Data tersedia ${formatDate(stats.data_range.from)} sampai ${formatDate(stats.data_range.to)}`
                    : 'Belum ada data penjualan'
            "
        >
            <template #actions>
                <div class="seg" role="group" aria-label="Periode">
                    <button
                        v-for="period in periods"
                        :key="period.days"
                        type="button"
                        class="seg-item"
                        :class="{ 'seg-item-active': filters.days === period.days }"
                        :aria-pressed="filters.days === period.days"
                        @click="visitWith({ days: period.days })"
                    >
                        {{ period.label }}
                    </button>
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
            </template>
        </PageHeader>

        <div class="mt-8">
            <StatStrip :items="kpis" />
        </div>

        <div class="mt-6 grid items-start gap-4 lg:grid-cols-3 [&>*]:min-w-0">
            <div class="min-w-0 lg:col-span-2">
                <Panel
                    title="Tren penjualan harian"
                    hint="Garis putus-putus: rata-rata bergerak 7 hari."
                >
                    <RevenueChart :points="stats.daily" :height="400" />
                </Panel>
            </div>

            <div class="flex min-w-0 flex-col gap-4">
                <Panel title="Jam tersibuk" hint="Jumlah struk per jam pada periode ini.">
                    <BarChart :items="hourItems" :height="132" />
                    <p v-if="busiestHour" class="mt-3 text-xs text-muted">
                        Puncak pada {{ String(busiestHour.hour).padStart(2, '0') }}:00 dengan
                        {{ formatNumber(busiestHour.transactions) }} struk.
                    </p>
                </Panel>

                <Panel title="Metode pembayaran" hint="Porsi jumlah struk, bukan nilai rupiah.">
                    <PaymentMix :items="stats.payments" />
                </Panel>
            </div>
        </div>

        <div class="mt-4 grid items-start gap-4 lg:grid-cols-3 [&>*]:min-w-0">
            <div class="min-w-0 lg:col-span-2">
                <Panel title="Transaksi terakhir" hint="Enam struk terbaru yang tercatat." >
                    <template #action>
                        <Link href="/transactions" class="link-inline text-xs">
                            Lihat semua
                        </Link>
                    </template>

                    <ul v-if="recent.length" class="divide-y divide-line">
                        <li v-for="row in recent" :key="row.id" class="grid grid-cols-[1fr_auto] gap-x-4 py-3 first:pt-0 last:pb-0">
                            <div class="min-w-0">
                                <p class="numeric text-2xs text-muted">{{ row.receipt_number ?? `#${row.id}` }}</p>
                                <p class="mt-0.5 truncate text-body text-ink">
                                    {{ row.items.map((item) => `${item.name} x${item.quantity}`).join(', ') }}
                                </p>
                            </div>
                            <div class="text-right">
                                <p class="numeric text-body font-medium text-ink">{{ formatCurrency(row.total_amount) }}</p>
                                <p class="text-2xs text-muted">
                                    {{ formatDateTime(row.occurred_at) }} · {{ row.outlet }}
                                </p>
                            </div>
                        </li>
                    </ul>
                    <p v-else class="py-8 text-center text-body text-muted">Belum ada transaksi.</p>
                </Panel>
            </div>

            <Panel title="Pola hari" hint="Total struk menurut hari dalam seminggu." >
                <BarChart :items="weekdayItems" :height="196" />
            </Panel>
        </div>

        <div class="mt-4 grid items-start gap-4 lg:grid-cols-3 [&>*]:min-w-0">
            <div class="min-w-0 lg:col-span-2">
                <Panel title="Stok perlu perhatian" hint="Saldo pada atau di bawah batas minimum." >
                    <template #action>
                        <Link href="/stock?status=low" class="link-inline text-xs">
                            Kelola stok
                        </Link>
                    </template>

                    <ul v-if="stats.low_stock.length" class="divide-y divide-line">
                        <li
                            v-for="row in stats.low_stock"
                            :key="`${row.outlet}-${row.product}`"
                            class="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
                        >
                            <div class="min-w-0">
                                <p class="truncate text-body text-ink">{{ row.product }}</p>
                                <p class="text-2xs text-muted">
                                    {{ row.outlet }} · minimum {{ formatNumber(row.min_quantity) }} {{ row.unit }}
                                </p>
                            </div>
                            <Badge variant="warning" class="numeric shrink-0">
                                {{ formatNumber(row.quantity) }} {{ row.unit }}
                            </Badge>
                        </li>
                    </ul>
                    <p v-else class="flex items-center gap-2 py-8 text-body text-muted">
                        <Icon name="check" :size="16" class="text-primary" />
                        Semua stok di atas batas minimum.
                    </p>
                </Panel>
            </div>

            <Panel title="Produk terlaris" hint="Delapan produk dengan unit terjual terbanyak." >
                <RankList :items="topProducts" />
            </Panel>
        </div>

        <div class="strip mt-6 sm:grid-cols-3">
            <div class="strip-cell">
                <p class="strip-label">Hari terakhir ada transaksi</p>
                <p class="strip-value">{{ formatCurrency(stats.last_sale.revenue) }}</p>
                <p class="text-2xs text-muted">
                    {{ stats.last_sale.date ? formatDate(stats.last_sale.date) : 'Belum ada data' }} ·
                    {{ formatNumber(stats.last_sale.transactions) }} struk
                </p>
            </div>
            <div class="strip-cell">
                <p class="strip-label">Unit di gudang</p>
                <p class="strip-value">{{ formatNumber(stats.inventory.units_on_hand) }}</p>
                <p class="text-2xs text-muted">
                    {{ stats.inventory.as_of ? `Saldo per ${formatDate(stats.inventory.as_of)}` : 'Belum ada pergerakan stok' }}
                </p>
            </div>
            <div class="strip-cell">
                <p class="strip-label">Rata-rata item per struk</p>
                <p class="strip-value">{{ itemsPerReceipt }}</p>
            </div>
        </div>
    </AppLayout>
</template>
