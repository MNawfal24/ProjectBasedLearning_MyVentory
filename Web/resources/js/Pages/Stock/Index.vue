<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { computed, ref } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/Components/ui/table';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import MultiBarChart from '../../Components/MultiBarChart.vue';
import PageHeader from '../../Components/PageHeader.vue';
import Pagination from '../../Components/Pagination.vue';
import Panel from '../../Components/Panel.vue';
import { formatDate, formatDateTime, formatNumber } from '../../format';
import { useChartColors, visitWith } from '../../ui';

const props = defineProps({
    stocks: { type: Object, required: true },
    movements: { type: Array, required: true },
    filters: { type: Object, required: true },
    outlets: { type: Array, required: true },
    products: { type: Array, required: true },
    summary: { type: Object, required: true },
    chart: { type: Object, required: true },
    as_of: { type: String, default: null },
});

const showMovement = ref(false);
const editing = ref(null);

const movementForm = useForm({
    outlet_id: props.outlets[0]?.id ?? null,
    product_id: props.products[0]?.id ?? null,
    type: 'in',
    quantity: 1,
    note: '',
    occurred_at: '',
});

const minimumForm = useForm({ min_quantity: 0 });

const typeLabels = {
    in: 'Stok masuk',
    out: 'Stok keluar',
    adjustment: 'Penyesuaian (stok opname)',
};

const movementHint = computed(() =>
    movementForm.type === 'adjustment'
        ? 'Isi saldo akhir hasil hitung fisik. Selisihnya dicatat sebagai satu penyesuaian.'
        : movementForm.type === 'in'
          ? 'Menambah saldo stok outlet dan produk yang dipilih.'
          : 'Mengurangi saldo stok, misalnya untuk barang rusak atau pemakaian internal.',
);

function submitMovement() {
    movementForm.post('/stock', {
        preserveScroll: true,
        onSuccess: () => {
            showMovement.value = false;
            movementForm.reset('quantity', 'note', 'occurred_at');
        },
    });
}

function openMinimum(stock) {
    editing.value = stock;
    minimumForm.min_quantity = stock.min_quantity;
    minimumForm.clearErrors();
}

function submitMinimum() {
    minimumForm.patch(`/stock/${editing.value.id}`, {
        preserveScroll: true,
        onSuccess: () => (editing.value = null),
    });
}

function statusOf(stock) {
    if (stock.quantity <= 0) {
        return { label: 'Habis', variant: 'destructive' };
    }
    if (stock.quantity <= stock.min_quantity) {
        return { label: 'Menipis', variant: 'warning' };
    }

    return { label: 'Aman', variant: 'default' };
}

const statuses = [
    { value: '', label: 'Semua' },
    { value: 'low', label: 'Menipis' },
    { value: 'out', label: 'Habis' },
];

const summaryCells = computed(() => [
    { label: 'Outlet × produk', value: formatNumber(props.summary.series), tone: 'text-ink' },
    { label: 'Menipis', value: formatNumber(props.summary.low), tone: 'text-accent' },
    { label: 'Habis', value: formatNumber(props.summary.out), tone: 'text-danger' },
    { label: 'Unit di gudang', value: formatNumber(props.summary.units), tone: 'text-ink' },
]);

const colors = useChartColors();

const buckets = [
    { key: 'safe', label: 'Aman' },
    { key: 'low', label: 'Menipis' },
    { key: 'out', label: 'Habis' },
];

const palette = computed(() => [colors.value.primary, colors.value.accent, colors.value.danger]);

const statusChart = computed(() => ({
    categories: props.chart.status.map((row) => row.outlet),
    series: buckets.map((bucket, index) => ({
        name: bucket.label,
        color: palette.value[index],
        data: props.chart.status.map((row) => row[bucket.key]),
    })),
}));

const balanceHint = computed(() =>
    props.as_of
        ? `Saldo per ${formatDate(props.as_of)}, dijumlah dari pergerakan stok yang tercatat.`
        : 'Belum ada pergerakan stok yang tercatat.',
);
</script>

<template>
    <Head title="Stock" />

    <AppLayout>
        <PageHeader
            title="Stock"
            description="Saldo per outlet dan produk, dihitung dari pergerakan stok yang tercatat."
        >
            <template #actions>
                <Button @click="showMovement = true">
                    <Icon name="plus" :size="16" />
                    Catat pergerakan
                </Button>
            </template>
        </PageHeader>

        <div class="strip mt-8 grid-cols-2 lg:grid-cols-4">
            <div v-for="cell in summaryCells" :key="cell.label" class="strip-cell">
                <p class="strip-label">{{ cell.label }}</p>
                <p class="strip-value" :class="cell.tone">{{ cell.value }}</p>
            </div>
        </div>

        <div class="mt-6">
            <Panel title="Komposisi status stok per outlet" :hint="balanceHint">
                <div class="mb-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted">
                    <span v-for="(bucket, index) in buckets" :key="bucket.key" class="flex items-center gap-2">
                        <span class="h-2.5 w-2.5 rounded-[3px]" :style="{ backgroundColor: palette[index] }"></span>
                        {{ bucket.label }} · {{ formatNumber(summary[bucket.key]) }}
                    </span>
                </div>
                <MultiBarChart
                    :categories="statusChart.categories"
                    :series="statusChart.series"
                    stack
                    horizontal
                    :height="200"
                    suffix=" seri"
                />
            </Panel>
        </div>

        <section class="panel mt-4">
            <header class="panel-head">
                <div class="min-w-0">
                    <h2 class="panel-title">Saldo stok</h2>
                    <p class="panel-hint">Satu baris per outlet dan produk. Filter ada di judul kolom.</p>
                </div>
            </header>

            <!-- Below md the header row is gone, so the same two filters move into a bar. -->
            <div class="flex gap-2 border-b border-line px-4 py-3 md:hidden">
                <div class="min-w-0 flex-1">
                    <Label for="stock-outlet-mobile" class="mb-1">Outlet</Label>
                    <select
                        id="stock-outlet-mobile"
                        class="field"
                        :value="filters.outlet ?? ''"
                        @change="visitWith({ outlet: $event.target.value || null, page: null })"
                    >
                        <option value="">Semua outlet</option>
                        <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                    </select>
                </div>
                <div class="min-w-0 flex-1">
                    <Label for="stock-status-mobile" class="mb-1">Status</Label>
                    <select
                        id="stock-status-mobile"
                        class="field"
                        :value="filters.status ?? ''"
                        @change="visitWith({ status: $event.target.value || null, page: null })"
                    >
                        <option v-for="status in statuses" :key="status.value" :value="status.value">
                            {{ status.label }}
                        </option>
                    </select>
                </div>
            </div>

            <template v-if="stocks.data.length">
                <!-- Below md the balance is the scanned figure, so it leads the row. -->
                <ul class="divide-y divide-line md:hidden">
                    <li v-for="row in stocks.data" :key="row.id" class="px-4 py-3">
                        <div class="flex items-baseline justify-between gap-3">
                            <span class="truncate text-body text-ink">{{ row.product }}</span>
                            <Badge :variant="statusOf(row).variant" class="shrink-0">{{ statusOf(row).label }}</Badge>
                        </div>
                        <p class="mt-1 text-2xs text-muted">
                            {{ row.outlet }} &middot; {{ row.sku ?? 'tanpa SKU' }} &middot; minimum
                            {{ formatNumber(row.min_quantity) }}
                        </p>
                        <div class="mt-1.5 flex items-baseline justify-between gap-3">
                            <span class="numeric text-body font-medium text-ink">
                                {{ formatNumber(row.quantity) }} <span class="text-xs text-muted">{{ row.unit }}</span>
                            </span>
                            <button type="button" class="link-inline text-xs" @click="openMinimum(row)">Atur minimum</button>
                        </div>
                    </li>
                </ul>

                <div class="hidden md:block">
                <Table>
                    <TableHeader>
                        <TableRow class="table-head-row hover:bg-surface-2">
                            <TableHead>Produk</TableHead>
                            <TableHead>SKU</TableHead>
                            <TableHead>
                                <div class="flex items-center gap-2">
                                    <span>Outlet</span>
                                    <select
                                        id="stock-outlet"
                                        class="field h-7 w-auto px-2 py-0 text-2xs"
                                        aria-label="Filter outlet"
                                        :value="filters.outlet ?? ''"
                                        @change="visitWith({ outlet: $event.target.value || null, page: null })"
                                    >
                                        <option value="">Semua</option>
                                        <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">
                                            {{ outlet.code }}
                                        </option>
                                    </select>
                                </div>
                            </TableHead>
                            <TableHead class="text-right">Saldo</TableHead>
                            <TableHead class="text-right">Minimum</TableHead>
                            <TableHead>
                                <div class="flex items-center gap-2">
                                    <span>Status</span>
                                    <select
                                        id="stock-status"
                                        class="field h-7 w-auto px-2 py-0 text-2xs"
                                        aria-label="Filter status"
                                        :value="filters.status ?? ''"
                                        @change="visitWith({ status: $event.target.value || null, page: null })"
                                    >
                                        <option v-for="status in statuses" :key="status.value" :value="status.value">
                                            {{ status.label }}
                                        </option>
                                    </select>
                                </div>
                            </TableHead>
                            <TableHead class="text-right">Aksi</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow v-for="row in stocks.data" :key="row.id">
                            <TableCell>{{ row.product }}</TableCell>
                            <TableCell class="numeric text-xs text-muted">{{ row.sku ?? '-' }}</TableCell>
                            <TableCell class="text-xs">{{ row.outlet }}</TableCell>
                            <TableCell class="numeric text-right">
                                {{ formatNumber(row.quantity) }} <span class="text-xs text-muted">{{ row.unit }}</span>
                            </TableCell>
                            <TableCell class="numeric text-right text-xs text-muted">{{ formatNumber(row.min_quantity) }}</TableCell>
                            <TableCell>
                                <Badge :variant="statusOf(row).variant">{{ statusOf(row).label }}</Badge>
                            </TableCell>
                            <TableCell class="text-right">
                                <Button variant="link" size="sm" class="h-auto p-0" @click="openMinimum(row)">Atur minimum</Button>
                            </TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
                </div>
            </template>

            <div v-else class="px-5 py-14 text-center">
                <p class="text-body text-muted">Tidak ada baris stok untuk filter ini.</p>
                <Button variant="outline" class="mt-3" @click="visitWith({ outlet: null, status: null, page: null })">
                    Hapus filter
                </Button>
            </div>

            <Pagination :paginator="stocks" label="baris stok" />
        </section>

        <section class="panel mt-4">
            <header class="panel-head">
                <div class="min-w-0">
                    <h2 class="panel-title">Pergerakan terakhir</h2>
                    <p class="panel-hint">Dua belas catatan terbaru, termasuk penjualan dari dashboard.</p>
                </div>
            </header>

            <ul v-if="movements.length" class="divide-y divide-line px-5">
                <li v-for="movement in movements" :key="movement.id" class="flex flex-wrap items-center justify-between gap-2 py-3">
                    <div class="min-w-0">
                        <p class="truncate text-body text-ink">{{ movement.product }}</p>
                        <p class="text-2xs text-muted">
                            {{ movement.outlet }} · {{ formatDateTime(movement.occurred_at) }}
                            <span v-if="movement.note">· {{ movement.note }}</span>
                        </p>
                    </div>
                    <div class="flex items-center gap-3">
                        <Badge variant="outline">{{ typeLabels[movement.type] ?? movement.type }}</Badge>
                        <span
                            class="numeric text-body font-medium"
                            :class="movement.quantity < 0 ? 'text-danger' : 'text-primary'"
                        >
                            {{ movement.quantity > 0 ? '+' : '' }}{{ formatNumber(movement.quantity) }} {{ movement.unit }}
                        </span>
                    </div>
                </li>
            </ul>
            <p v-else class="px-5 py-12 text-center text-body text-muted">Belum ada pergerakan stok.</p>
        </section>

        <Modal
            :open="showMovement"
            title="Catat pergerakan stok"
            :description="movementHint"
            @close="showMovement = false"
        >
            <form class="space-y-4" @submit.prevent="submitMovement">
                <div class="grid gap-3 sm:grid-cols-2">
                    <div>
                        <Label for="move-outlet" class="mb-1">Outlet</Label>
                        <select id="move-outlet" v-model="movementForm.outlet_id" class="field">
                            <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                        </select>
                    </div>
                    <div>
                        <Label for="move-type" class="mb-1">Jenis</Label>
                        <select id="move-type" v-model="movementForm.type" class="field">
                            <option v-for="(label, value) in typeLabels" :key="value" :value="value">{{ label }}</option>
                        </select>
                    </div>
                    <div class="sm:col-span-2">
                        <Label for="move-product" class="mb-1">Produk</Label>
                        <select id="move-product" v-model="movementForm.product_id" class="field">
                            <option v-for="product in products" :key="product.id" :value="product.id">
                                {{ product.name }}{{ product.sku ? ` (${product.sku})` : '' }}
                            </option>
                        </select>
                        <p v-if="movementForm.errors.product_id" class="mt-1 text-xs text-danger">
                            {{ movementForm.errors.product_id }}
                        </p>
                    </div>
                    <div>
                        <Label for="move-qty" class="mb-1">
                            {{ movementForm.type === 'adjustment' ? 'Saldo akhir' : 'Jumlah' }}
                        </Label>
                        <Input id="move-qty" v-model="movementForm.quantity" type="number" min="0" step="1" />
                        <p v-if="movementForm.errors.quantity" class="mt-1 text-xs text-danger">
                            {{ movementForm.errors.quantity }}
                        </p>
                    </div>
                    <div>
                        <Label for="move-time" class="mb-1">Waktu (opsional)</Label>
                        <Input id="move-time" v-model="movementForm.occurred_at" type="datetime-local" />
                    </div>
                    <div class="sm:col-span-2">
                        <Label for="move-note" class="mb-1">Catatan (opsional)</Label>
                        <Input id="move-note" v-model="movementForm.note" type="text" maxlength="255" />
                    </div>
                </div>

                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <Button variant="outline" @click="showMovement = false">Batal</Button>
                    <Button type="submit" :disabled="movementForm.processing">Simpan</Button>
                </div>
            </form>
        </Modal>

        <Modal
            :open="editing !== null"
            title="Batas minimum stok"
            description="Dashboard menandai baris ini sebagai menipis ketika saldo berada pada atau di bawah batas."
            @close="editing = null"
        >
            <form class="space-y-4" @submit.prevent="submitMinimum">
                <p class="text-body text-ink">{{ editing?.product }} · {{ editing?.outlet }}</p>
                <div>
                    <Label for="min-qty" class="mb-1">Minimum ({{ editing?.unit }})</Label>
                    <Input id="min-qty" v-model="minimumForm.min_quantity" type="number" min="0" step="1" />
                    <p v-if="minimumForm.errors.min_quantity" class="mt-1 text-xs text-danger">
                        {{ minimumForm.errors.min_quantity }}
                    </p>
                </div>
                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <Button variant="outline" @click="editing = null">Batal</Button>
                    <Button type="submit" :disabled="minimumForm.processing">Simpan</Button>
                </div>
            </form>
        </Modal>
    </AppLayout>
</template>
