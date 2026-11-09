<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { computed, ref, watch } from 'vue';
import { Button } from '@/Components/ui/button';
import { Card, CardContent } from '@/Components/ui/card';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/Components/ui/table';
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
            <Button @click="showForm = true">
                <Icon name="plus" :size="16" />
                Catat penjualan
            </Button>
        </header>

        <Card class="mt-6 gap-0">
            <CardContent class="flex flex-wrap items-end gap-3 border-b border-line">
                <div class="min-w-[12rem] flex-1">
                    <Label for="search" class="mb-1">Cari nomor struk</Label>
                    <div class="relative">
                        <span class="pointer-events-none absolute left-3 top-2.5 text-muted"><Icon name="search" :size="16" /></span>
                        <Input id="search" v-model="search" type="search" class="pl-9" placeholder="SHOP001JAN25..." />
                    </div>
                </div>

                <div>
                    <Label for="outlet" class="mb-1">Outlet</Label>
                    <select
                        id="outlet"
                        class="field w-auto"
                        :value="filters.outlet ?? ''"
                        @change="visitWith({ outlet: $event.target.value || null, page: null })"
                    >
                        <option value="">Semua</option>
                        <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                    </select>
                </div>

                <div>
                    <Label for="payment" class="mb-1">Pembayaran</Label>
                    <select
                        id="payment"
                        class="field w-auto"
                        :value="filters.payment ?? ''"
                        @change="visitWith({ payment: $event.target.value || null, page: null })"
                    >
                        <option value="">Semua</option>
                        <option v-for="payment in payments" :key="payment" :value="payment">{{ payment }}</option>
                    </select>
                </div>

                <div>
                    <Label for="from" class="mb-1">Dari</Label>
                    <Input
                        id="from"
                        type="date"
                        class="w-auto"
                        :model-value="filters.from"
                        @update:model-value="visitWith({ from: $event || null, page: null })"
                    />
                </div>

                <div>
                    <Label for="to" class="mb-1">Sampai</Label>
                    <Input
                        id="to"
                        type="date"
                        class="w-auto"
                        :model-value="filters.to"
                        @update:model-value="visitWith({ to: $event || null, page: null })"
                    />
                </div>

                <Button variant="outline" @click="resetFilters">Reset</Button>
            </CardContent>

            <template v-if="transactions.data.length">
                <Table>
                    <TableHeader>
                        <TableRow class="hover:bg-transparent">
                            <TableHead>Struk</TableHead>
                            <TableHead>Waktu</TableHead>
                            <TableHead>Outlet</TableHead>
                            <TableHead>Item</TableHead>
                            <TableHead>Pembayaran</TableHead>
                            <TableHead class="text-right">Bersih</TableHead>
                            <TableHead class="text-right">Total</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow v-for="row in transactions.data" :key="row.id">
                            <TableCell class="numeric whitespace-nowrap text-xs text-muted">{{ row.receipt_number ?? `#${row.id}` }}</TableCell>
                            <TableCell class="whitespace-nowrap text-xs">{{ formatDateTime(row.occurred_at) }}</TableCell>
                            <TableCell class="text-xs">{{ row.outlet }}</TableCell>
                            <TableCell class="max-w-[22rem] text-xs text-muted">
                                {{ row.items.map((item) => `${item.name} x${item.quantity}`).join(', ') }}
                            </TableCell>
                            <TableCell class="text-xs">
                                {{ row.payment_method }}
                                <span v-if="row.uses_loyalty_card" class="ml-1 rounded-md bg-primary-soft px-1.5 py-0.5 text-[10px] font-medium text-primary">
                                    loyalitas
                                </span>
                            </TableCell>
                            <TableCell class="numeric text-right text-xs">{{ formatCurrency(row.net_sales) }}</TableCell>
                            <TableCell class="numeric text-right">{{ formatCurrency(row.total_amount) }}</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </template>

            <div v-else class="px-4 py-12 text-center">
                <p class="text-sm text-muted">Tidak ada transaksi yang cocok dengan filter ini.</p>
                <Button variant="outline" class="mt-3" @click="resetFilters">Hapus filter</Button>
            </div>

            <Pagination :paginator="transactions" label="struk" />
        </Card>

        <Modal
            :open="showForm"
            title="Catat penjualan"
            description="Transaksi manual mengurangi stok outlet yang dipilih dan langsung masuk ke ringkasan."
            @close="showForm = false"
        >
            <form class="space-y-4" @submit.prevent="submit">
                <div class="grid gap-3 sm:grid-cols-2">
                    <div>
                        <Label for="form-outlet" class="mb-1">Outlet</Label>
                        <select id="form-outlet" v-model="form.outlet_id" class="field">
                            <option v-for="outlet in outlets" :key="outlet.id" :value="outlet.id">{{ outlet.code }}</option>
                        </select>
                        <p v-if="errorFor('outlet_id')" class="mt-1 text-xs text-danger">{{ errorFor('outlet_id') }}</p>
                    </div>
                    <div>
                        <Label for="form-time" class="mb-1">Waktu</Label>
                        <Input id="form-time" v-model="form.occurred_at" type="datetime-local" />
                        <p v-if="errorFor('occurred_at')" class="mt-1 text-xs text-danger">{{ errorFor('occurred_at') }}</p>
                    </div>
                    <div>
                        <Label for="form-payment" class="mb-1">Pembayaran</Label>
                        <select id="form-payment" v-model="form.payment_method" class="field">
                            <option v-for="payment in payments" :key="payment" :value="payment">{{ payment }}</option>
                        </select>
                    </div>
                    <div class="flex items-end pb-2">
                        <Label class="flex items-center gap-2 text-sm text-ink">
                            <input v-model="form.uses_loyalty_card" type="checkbox" class="h-4 w-4 rounded border-line" />
                            Kartu loyalitas
                        </Label>
                    </div>
                </div>

                <div>
                    <div class="mb-2 flex items-center justify-between">
                        <span class="text-xs text-muted">Item</span>
                        <Button variant="link" size="sm" class="h-auto p-0" @click="addLine">Tambah item</Button>
                    </div>

                    <div class="space-y-2">
                        <div v-for="(line, index) in form.items" :key="index" class="flex items-start gap-2">
                            <div class="flex-1">
                                <Label class="sr-only" :for="`product-${index}`">Produk {{ index + 1 }}</Label>
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
                                <Label class="sr-only" :for="`qty-${index}`">Jumlah {{ index + 1 }}</Label>
                                <Input :id="`qty-${index}`" v-model="line.quantity" type="number" min="1" max="999" />
                                <p v-if="errorFor(`items.${index}.quantity`)" class="mt-1 text-xs text-danger">
                                    {{ errorFor(`items.${index}.quantity`) }}
                                </p>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                class="mt-1 hover:text-danger"
                                :disabled="form.items.length === 1"
                                aria-label="Hapus item"
                                @click="removeLine(index)"
                            >
                                <Icon name="close" :size="16" />
                            </Button>
                        </div>
                    </div>
                    <p v-if="errorFor('items')" class="mt-1 text-xs text-danger">{{ errorFor('items') }}</p>
                </div>

                <div>
                    <Label for="form-note" class="mb-1">Catatan (opsional)</Label>
                    <Input id="form-note" v-model="form.note" type="text" maxlength="255" />
                </div>

                <div class="flex items-center justify-between border-t border-line pt-3">
                    <div>
                        <p class="text-xs text-muted">Bersih sebelum pajak</p>
                        <p class="numeric text-base font-semibold text-ink">{{ formatCurrency(previewTotal) }}</p>
                    </div>
                    <div class="flex gap-2">
                        <Button variant="outline" @click="showForm = false">Batal</Button>
                        <Button type="submit" :disabled="form.processing">
                            {{ form.processing ? 'Menyimpan...' : 'Simpan transaksi' }}
                        </Button>
                    </div>
                </div>
            </form>
        </Modal>
    </AppLayout>
</template>
