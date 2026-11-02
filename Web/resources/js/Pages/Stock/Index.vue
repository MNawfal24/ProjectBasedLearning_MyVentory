<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { computed, ref } from 'vue';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import Pagination from '../../Components/Pagination.vue';
import { formatDateTime, formatNumber } from '../../format';
import { visitWith } from '../../ui';

const props = defineProps({
    stocks: { type: Object, required: true },
    movements: { type: Array, required: true },
    filters: { type: Object, required: true },
    outlets: { type: Array, required: true },
    products: { type: Array, required: true },
    summary: { type: Object, required: true },
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
        return { label: 'Habis', class: 'bg-danger-soft text-danger' };
    }
    if (stock.quantity <= stock.min_quantity) {
        return { label: 'Menipis', class: 'bg-accent-soft text-accent' };
    }

    return { label: 'Aman', class: 'bg-primary-soft text-primary' };
}

const statuses = [
    { value: '', label: 'Semua' },
    { value: 'low', label: 'Menipis' },
    { value: 'out', label: 'Habis' },
];
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
            <button type="button" class="btn" @click="showMovement = true">
                <Icon name="plus" :size="16" />
                Catat pergerakan
            </button>
        </header>

        <div class="mt-6 grid grid-cols-2 rounded-xl border border-line bg-surface lg:grid-cols-4">
            <div class="px-5 py-4">
                <p class="text-xs text-muted">Seri stok</p>
                <p class="numeric mt-1 text-2xl font-semibold text-ink">{{ formatNumber(summary.series) }}</p>
            </div>
            <div class="border-l border-line px-5 py-4">
                <p class="text-xs text-muted">Menipis</p>
                <p class="numeric mt-1 text-2xl font-semibold text-accent">{{ formatNumber(summary.low) }}</p>
            </div>
            <div class="border-t border-line px-5 py-4 lg:border-l lg:border-t-0">
                <p class="text-xs text-muted">Habis</p>
                <p class="numeric mt-1 text-2xl font-semibold text-danger">{{ formatNumber(summary.out) }}</p>
            </div>
            <div class="border-l border-t border-line px-5 py-4 lg:border-t-0">
                <p class="text-xs text-muted">Unit di gudang</p>
                <p class="numeric mt-1 text-2xl font-semibold text-ink">{{ formatNumber(summary.units) }}</p>
            </div>
        </div>

        <section class="mt-4 rounded-xl border border-line bg-surface">
            <div class="flex flex-wrap items-end gap-3 border-b border-line p-4">
                <div>
                    <label class="mb-1 block text-xs text-muted" for="stock-outlet">Outlet</label>
                    <select
                        id="stock-outlet"
                        class="field"
                        :value="filters.outlet ?? ''"
                        @change="visitWith({ outlet: $event.target.value || null, page: null })"
                    >
                        <option value="">Semua</option>
                        <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                    </select>
                </div>

                <div class="flex items-center gap-1 rounded-lg border border-line p-1" role="group" aria-label="Status stok">
                    <button
                        v-for="status in statuses"
                        :key="status.value"
                        type="button"
                        class="chip"
                        :class="filters.status === status.value ? 'chip-active' : 'chip-idle'"
                        :aria-pressed="filters.status === status.value"
                        @click="visitWith({ status: status.value || null, page: null })"
                    >
                        {{ status.label }}
                    </button>
                </div>

                <p class="ml-auto text-xs text-muted">
                    Saldo awal berasal dari kecepatan penjualan 14 hari terakhir, karena ekspor kasir tidak memuat jumlah stok.
                </p>
            </div>

            <div v-if="stocks.data.length" class="overflow-x-auto">
                <table class="w-full border-collapse">
                    <thead>
                        <tr class="border-b border-line">
                            <th class="th">Produk</th>
                            <th class="th">SKU</th>
                            <th class="th">Outlet</th>
                            <th class="th text-right">Saldo</th>
                            <th class="th text-right">Minimum</th>
                            <th class="th">Status</th>
                            <th class="th text-right">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="row in stocks.data"
                            :key="row.id"
                            class="border-b border-dashed border-line last:border-0 hover:bg-surface-2"
                        >
                            <td class="td">{{ row.product }}</td>
                            <td class="td numeric text-xs text-muted">{{ row.sku ?? '-' }}</td>
                            <td class="td text-xs">{{ row.outlet }}</td>
                            <td class="td numeric text-right">
                                {{ formatNumber(row.quantity) }} <span class="text-xs text-muted">{{ row.unit }}</span>
                            </td>
                            <td class="td numeric text-right text-xs text-muted">{{ formatNumber(row.min_quantity) }}</td>
                            <td class="td">
                                <span class="rounded-md px-2 py-0.5 text-xs font-medium" :class="statusOf(row).class">
                                    {{ statusOf(row).label }}
                                </span>
                            </td>
                            <td class="td text-right">
                                <button
                                    type="button"
                                    class="text-xs font-medium text-primary hover:underline"
                                    @click="openMinimum(row)"
                                >
                                    Atur minimum
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-else class="px-4 py-12 text-center text-sm text-muted">
                Tidak ada baris stok untuk filter ini.
            </div>

            <Pagination :paginator="stocks" label="baris stok" />
        </section>

        <section class="mt-4 rounded-xl border border-line bg-surface">
            <header class="border-b border-line px-5 py-4">
                <h2 class="text-sm font-semibold text-ink">Pergerakan terakhir</h2>
                <p class="mt-1 text-xs text-muted">Dua belas catatan terbaru, termasuk penjualan dari dashboard.</p>
            </header>

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
                        <span class="text-xs text-muted">{{ typeLabels[movement.type] ?? movement.type }}</span>
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
                        <label class="mb-1 block text-xs text-muted" for="move-outlet">Outlet</label>
                        <select id="move-outlet" v-model="movementForm.outlet_id" class="field">
                            <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                        </select>
                    </div>
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="move-type">Jenis</label>
                        <select id="move-type" v-model="movementForm.type" class="field">
                            <option v-for="(label, value) in typeLabels" :key="value" :value="value">{{ label }}</option>
                        </select>
                    </div>
                    <div class="sm:col-span-2">
                        <label class="mb-1 block text-xs text-muted" for="move-product">Produk</label>
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
                        <label class="mb-1 block text-xs text-muted" for="move-qty">
                            {{ movementForm.type === 'adjustment' ? 'Saldo akhir' : 'Jumlah' }}
                        </label>
                        <input id="move-qty" v-model="movementForm.quantity" type="number" min="0" step="1" class="field" />
                        <p v-if="movementForm.errors.quantity" class="mt-1 text-xs text-danger">
                            {{ movementForm.errors.quantity }}
                        </p>
                    </div>
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="move-time">Waktu (opsional)</label>
                        <input id="move-time" v-model="movementForm.occurred_at" type="datetime-local" class="field" />
                    </div>
                    <div class="sm:col-span-2">
                        <label class="mb-1 block text-xs text-muted" for="move-note">Catatan (opsional)</label>
                        <input id="move-note" v-model="movementForm.note" type="text" maxlength="255" class="field" />
                    </div>
                </div>

                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <button type="button" class="btn-quiet" @click="showMovement = false">Batal</button>
                    <button type="submit" class="btn" :disabled="movementForm.processing">Simpan</button>
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
                    <label class="mb-1 block text-xs text-muted" for="min-qty">Minimum ({{ editing?.unit }})</label>
                    <input id="min-qty" v-model="minimumForm.min_quantity" type="number" min="0" step="1" class="field" />
                    <p v-if="minimumForm.errors.min_quantity" class="mt-1 text-xs text-danger">
                        {{ minimumForm.errors.min_quantity }}
                    </p>
                </div>
                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <button type="button" class="btn-quiet" @click="editing = null">Batal</button>
                    <button type="submit" class="btn" :disabled="minimumForm.processing">Simpan</button>
                </div>
            </form>
        </Modal>
    </AppLayout>
</template>
