<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { computed, ref } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { Button } from '@/Components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/Components/ui/card';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/Components/ui/table';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import MultiBarChart from '../../Components/MultiBarChart.vue';
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

const summaryCards = computed(() => [
    { label: 'Outlet × produk', value: props.summary.series, class: 'text-ink' },
    { label: 'Menipis', value: props.summary.low, class: 'text-accent' },
    { label: 'Habis', value: props.summary.out, class: 'text-danger' },
    { label: 'Unit di gudang', value: props.summary.units, class: 'text-ink' },
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
        <header class="flex flex-wrap items-end justify-between gap-4">
            <div>
                <h1 class="text-2xl font-semibold tracking-tight text-ink">Stock</h1>
                <p class="mt-1 text-sm text-muted">
                    Saldo per outlet dan produk, dihitung dari pergerakan stok yang tercatat.
                </p>
            </div>
            <Button @click="showMovement = true">
                <Icon name="plus" :size="16" />
                Catat pergerakan
            </Button>
        </header>

        <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card v-for="cell in summaryCards" :key="cell.label">
                <CardHeader class="gap-1">
                    <CardDescription>{{ cell.label }}</CardDescription>
                    <CardTitle class="numeric text-2xl" :class="cell.class">{{ formatNumber(cell.value) }}</CardTitle>
                </CardHeader>
            </Card>
        </div>

        <div class="mt-4">
            <Panel title="Komposisi status stok per outlet" :hint="balanceHint">
                <div class="mb-3 flex flex-wrap items-center gap-4 text-xs text-muted">
                    <span v-for="(bucket, index) in buckets" :key="bucket.key" class="flex items-center gap-2">
                        <span class="h-2.5 w-2.5 rounded-sm" :style="{ backgroundColor: palette[index] }"></span>
                        {{ bucket.label }} · {{ formatNumber(summary[bucket.key]) }}
                    </span>
                </div>
                <MultiBarChart
                    :categories="statusChart.categories"
                    :series="statusChart.series"
                    stack
                    horizontal
                    :height="150"
                    suffix=" seri"
                />
            </Panel>
        </div>

        <Card class="mt-4">
            <CardHeader class="border-b border-line py-4">
                <CardTitle>Saldo stok</CardTitle>
                <CardDescription>Satu baris per outlet dan produk. Filter ada di judul kolom.</CardDescription>
            </CardHeader>

            <template v-if="stocks.data.length">
                <Table>
                    <TableHeader>
                        <TableRow class="hover:bg-transparent">
                            <TableHead>Produk</TableHead>
                            <TableHead>SKU</TableHead>
                            <TableHead>
                                <div class="flex items-center gap-2">
                                    <span>Outlet</span>
                                    <select
                                        id="stock-outlet"
                                        class="field h-7 w-auto px-2 py-0 text-xs"
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
                                        class="field h-7 w-auto px-2 py-0 text-xs"
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
            </template>

            <div v-else class="px-4 py-12 text-center text-sm text-muted">
                Tidak ada baris stok untuk filter ini.
            </div>

            <Pagination :paginator="stocks" label="baris stok" />
        </Card>

        <Card class="mt-4">
            <CardHeader class="border-b border-line py-4">
                <CardTitle>Pergerakan terakhir</CardTitle>
                <CardDescription>Dua belas catatan terbaru, termasuk penjualan dari dashboard.</CardDescription>
            </CardHeader>

            <ul v-if="movements.length" class="divide-y divide-dashed divide-line px-5">
                <li v-for="movement in movements" :key="movement.id" class="flex flex-wrap items-center justify-between gap-2 py-3">
                    <div class="min-w-0">
                        <p class="truncate text-sm text-ink">{{ movement.product }}</p>
                        <p class="text-xs text-muted">
                            {{ movement.outlet }} · {{ formatDateTime(movement.occurred_at) }}
                            <span v-if="movement.note">· {{ movement.note }}</span>
                        </p>
                    </div>
                    <div class="flex items-center gap-3">
                        <Badge variant="outline">{{ typeLabels[movement.type] ?? movement.type }}</Badge>
                        <span
                            class="numeric text-sm font-medium"
                            :class="movement.quantity < 0 ? 'text-danger' : 'text-primary'"
                        >
                            {{ movement.quantity > 0 ? '+' : '' }}{{ formatNumber(movement.quantity) }} {{ movement.unit }}
                        </span>
                    </div>
                </li>
            </ul>
            <p v-else class="px-5 py-10 text-center text-sm text-muted">Belum ada pergerakan stok.</p>
        </Card>

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
                <p class="text-sm text-ink">{{ editing?.product }} · {{ editing?.outlet }}</p>
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
