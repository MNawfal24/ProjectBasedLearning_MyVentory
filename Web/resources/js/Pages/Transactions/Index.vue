<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { computed, ref, watch } from 'vue';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import Pagination from '../../Components/Pagination.vue';
import { formatCurrency, formatDateTime, formatNumber } from '../../format';
import { visitWith } from '../../ui';

const props = defineProps({
    transactions: { type: Object, required: true },
    filters: { type: Object, required: true },
    outlets: { type: Array, required: true },
    payments: { type: Array, required: true },
    products: { type: Array, required: true },
});

const search = ref(props.filters.search ?? '');
const showForm = ref(false);

let searchTimer = null;
watch(search, (value) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => visitWith({ search: value, page: null }), 350);
});

const nowLocal = () => {
    const now = new Date();
    const offset = now.getTimezoneOffset() * 60000;

    return new Date(now - offset).toISOString().slice(0, 16);
};

const form = useForm({
    outlet_id: props.outlets[0]?.id ?? null,
    occurred_at: nowLocal(),
    payment_method: props.payments[0] ?? 'Cash',
    uses_loyalty_card: false,
    note: '',
    items: [{ product_id: props.products[0]?.id ?? null, quantity: 1 }],
});

const priceOf = (productId) => Number(props.products.find((product) => product.id === productId)?.sell_price ?? 0);

const previewTotal = computed(() =>
    form.items.reduce((sum, line) => sum + priceOf(line.product_id) * (Number(line.quantity) || 0), 0),
);

function addLine() {
    form.items.push({ product_id: props.products[0]?.id ?? null, quantity: 1 });
}

function removeLine(index) {
    if (form.items.length > 1) {
        form.items.splice(index, 1);
    }
}

function submit() {
    form.post('/transactions', {
        preserveScroll: true,
        onSuccess: () => {
            showForm.value = false;
            form.reset('items', 'note');
            form.occurred_at = nowLocal();
            form.items = [{ product_id: props.products[0]?.id ?? null, quantity: 1 }];
        },
    });
}

function resetFilters() {
    search.value = '';
    visitWith({ search: null, outlet: null, payment: null, from: null, to: null, page: null });
}

const errorFor = (key) => form.errors[key];
</script>

<template>
    <Head title="Transactions" />

    <AppLayout>
        <header class="flex flex-wrap items-end justify-between gap-4">
            <div>
                <h1 class="text-2xl font-semibold tracking-tight text-ink">Transactions</h1>
                <p class="mt-1 text-sm text-muted">
                    {{ formatNumber(transactions.total) }} struk tercatat, {{ formatNumber(products.length) }} produk aktif
                </p>
            </div>
            <button type="button" class="btn" @click="showForm = true">
                <Icon name="plus" :size="16" />
                Catat penjualan
            </button>
        </header>

        <section class="mt-6 rounded-xl border border-line bg-surface">
            <div class="flex flex-wrap items-end gap-3 border-b border-line p-4">
                <div class="min-w-[12rem] flex-1">
                    <label class="mb-1 block text-xs text-muted" for="search">Cari nomor struk</label>
                    <div class="relative">
                        <span class="pointer-events-none absolute left-3 top-2.5 text-muted"><Icon name="search" :size="16" /></span>
                        <input id="search" v-model="search" type="search" class="field pl-9" placeholder="SHOP001JAN25..." />
                    </div>
                </div>

                <div>
                    <label class="mb-1 block text-xs text-muted" for="outlet">Outlet</label>
                    <select
                        id="outlet"
                        class="field"
                        :value="filters.outlet ?? ''"
                        @change="visitWith({ outlet: $event.target.value || null, page: null })"
                    >
                        <option value="">Semua</option>
                        <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                    </select>
                </div>

                <div>
                    <label class="mb-1 block text-xs text-muted" for="payment">Pembayaran</label>
                    <select
                        id="payment"
                        class="field"
                        :value="filters.payment ?? ''"
                        @change="visitWith({ payment: $event.target.value || null, page: null })"
                    >
                        <option value="">Semua</option>
                        <option v-for="payment in payments" :key="payment" :value="payment">{{ payment }}</option>
                    </select>
                </div>

                <div>
                    <label class="mb-1 block text-xs text-muted" for="from">Dari</label>
                    <input
                        id="from"
                        type="date"
                        class="field"
                        :value="filters.from"
                        @change="visitWith({ from: $event.target.value || null, page: null })"
                    />
                </div>

                <div>
                    <label class="mb-1 block text-xs text-muted" for="to">Sampai</label>
                    <input
                        id="to"
                        type="date"
                        class="field"
                        :value="filters.to"
                        @change="visitWith({ to: $event.target.value || null, page: null })"
                    />
                </div>

                <button type="button" class="btn-quiet" @click="resetFilters">Reset</button>
            </div>

            <div v-if="transactions.data.length" class="overflow-x-auto">
                <table class="w-full border-collapse">
                    <thead>
                        <tr class="border-b border-line">
                            <th class="th">Struk</th>
                            <th class="th">Waktu</th>
                            <th class="th">Outlet</th>
                            <th class="th">Item</th>
                            <th class="th">Pembayaran</th>
                            <th class="th text-right">Bersih</th>
                            <th class="th text-right">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="row in transactions.data"
                            :key="row.id"
                            class="border-b border-dashed border-line last:border-0 hover:bg-surface-2"
                        >
                            <td class="td numeric whitespace-nowrap text-xs text-muted">{{ row.receipt_number ?? `#${row.id}` }}</td>
                            <td class="td whitespace-nowrap text-xs">{{ formatDateTime(row.occurred_at) }}</td>
                            <td class="td text-xs">{{ row.outlet }}</td>
                            <td class="td max-w-[22rem] text-xs text-muted">
                                {{ row.items.map((item) => `${item.name} x${item.quantity}`).join(', ') }}
                            </td>
                            <td class="td text-xs">
                                {{ row.payment_method }}
                                <span v-if="row.uses_loyalty_card" class="ml-1 rounded-md bg-primary-soft px-1.5 py-0.5 text-[10px] font-medium text-primary">
                                    loyalitas
                                </span>
                            </td>
                            <td class="td numeric text-right text-xs">{{ formatCurrency(row.net_sales) }}</td>
                            <td class="td numeric text-right">{{ formatCurrency(row.total_amount) }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-else class="px-4 py-12 text-center">
                <p class="text-sm text-muted">Tidak ada transaksi yang cocok dengan filter ini.</p>
                <button type="button" class="btn-quiet mt-3" @click="resetFilters">Hapus filter</button>
            </div>

            <Pagination :paginator="transactions" label="struk" />
        </section>

        <Modal
            :open="showForm"
            title="Catat penjualan"
            description="Transaksi manual mengurangi stok outlet yang dipilih dan langsung masuk ke ringkasan."
            @close="showForm = false"
        >
            <form class="space-y-4" @submit.prevent="submit">
                <div class="grid gap-3 sm:grid-cols-2">
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="form-outlet">Outlet</label>
                        <select id="form-outlet" v-model="form.outlet_id" class="field">
                            <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                        </select>
                        <p v-if="errorFor('outlet_id')" class="mt-1 text-xs text-danger">{{ errorFor('outlet_id') }}</p>
                    </div>
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="form-time">Waktu</label>
                        <input id="form-time" v-model="form.occurred_at" type="datetime-local" class="field" />
                        <p v-if="errorFor('occurred_at')" class="mt-1 text-xs text-danger">{{ errorFor('occurred_at') }}</p>
                    </div>
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="form-payment">Pembayaran</label>
                        <select id="form-payment" v-model="form.payment_method" class="field">
                            <option v-for="payment in payments" :key="payment" :value="payment">{{ payment }}</option>
                        </select>
                    </div>
                    <div class="flex items-end pb-2">
                        <label class="flex items-center gap-2 text-sm text-ink">
                            <input v-model="form.uses_loyalty_card" type="checkbox" class="h-4 w-4 rounded border-line" />
                            Kartu loyalitas
                        </label>
                    </div>
                </div>

                <div>
                    <div class="mb-2 flex items-center justify-between">
                        <span class="text-xs text-muted">Item</span>
                        <button type="button" class="text-xs font-medium text-primary hover:underline" @click="addLine">
                            Tambah item
                        </button>
                    </div>

                    <div class="space-y-2">
                        <div v-for="(line, index) in form.items" :key="index" class="flex items-start gap-2">
                            <div class="flex-1">
                                <label class="sr-only" :for="`product-${index}`">Produk {{ index + 1 }}</label>
                                <select :id="`product-${index}`" v-model="line.product_id" class="field">
                                    <option v-for="product in products" :key="product.id" :value="product.id">
                                        {{ product.name }}
                                    </option>
                                </select>
                                <p v-if="errorFor(`items.${index}.product_id`)" class="mt-1 text-xs text-danger">
                                    {{ errorFor(`items.${index}.product_id`) }}
                                </p>
                            </div>
                            <div class="w-24">
                                <label class="sr-only" :for="`qty-${index}`">Jumlah {{ index + 1 }}</label>
                                <input :id="`qty-${index}`" v-model="line.quantity" type="number" min="1" max="999" class="field" />
                                <p v-if="errorFor(`items.${index}.quantity`)" class="mt-1 text-xs text-danger">
                                    {{ errorFor(`items.${index}.quantity`) }}
                                </p>
                            </div>
                            <button
                                type="button"
                                class="mt-1 rounded-lg p-2 text-muted hover:bg-surface-2 hover:text-danger"
                                :disabled="form.items.length === 1"
                                aria-label="Hapus item"
                                @click="removeLine(index)"
                            >
                                <Icon name="close" :size="16" />
                            </button>
                        </div>
                    </div>
                    <p v-if="errorFor('items')" class="mt-1 text-xs text-danger">{{ errorFor('items') }}</p>
                </div>

                <div>
                    <label class="mb-1 block text-xs text-muted" for="form-note">Catatan (opsional)</label>
                    <input id="form-note" v-model="form.note" type="text" class="field" maxlength="255" />
                </div>

                <div class="flex items-center justify-between border-t border-line pt-3">
                    <div>
                        <p class="text-xs text-muted">Bersih sebelum pajak</p>
                        <p class="numeric text-base font-semibold text-ink">{{ formatCurrency(previewTotal) }}</p>
                    </div>
                    <div class="flex gap-2">
                        <button type="button" class="btn-quiet" @click="showForm = false">Batal</button>
                        <button type="submit" class="btn" :disabled="form.processing">
                            {{ form.processing ? 'Menyimpan...' : 'Simpan transaksi' }}
                        </button>
                    </div>
                </div>
            </form>
        </Modal>
    </AppLayout>
</template>
