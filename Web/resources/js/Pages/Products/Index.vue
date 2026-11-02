<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { ref, watch } from 'vue';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import { formatCurrency, formatNumber } from '../../format';
import { visitWith } from '../../ui';

const props = defineProps({
    products: { type: Array, required: true },
    filters: { type: Object, required: true },
});

const search = ref(props.filters.search ?? '');
const editing = ref(null);
const showForm = ref(false);

let searchTimer = null;
watch(search, (value) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => visitWith({ search: value }), 350);
});

const form = useForm({
    name: '',
    sku: '',
    category: '',
    unit: 'pcs',
    sell_price: 0,
    is_active: true,
});

function openCreate() {
    editing.value = null;
    form.reset();
    form.clearErrors();
    showForm.value = true;
}

function openEdit(product) {
    editing.value = product;
    form.name = product.name;
    form.sku = product.sku;
    form.category = product.category ?? '';
    form.unit = product.unit;
    form.sell_price = product.sell_price;
    form.is_active = product.is_active;
    form.clearErrors();
    showForm.value = true;
}

function submit() {
    const options = {
        preserveScroll: true,
        onSuccess: () => {
            showForm.value = false;
            form.reset();
        },
    };

    if (editing.value) {
        form.patch(`/products/${editing.value.id}`, options);
    } else {
        form.post('/products', options);
    }
}
</script>

<template>
    <Head title="Products" />

    <AppLayout>
        <header class="flex flex-wrap items-end justify-between gap-4">
            <div>
                <h1 class="text-2xl font-semibold tracking-tight text-ink">Products</h1>
                <p class="mt-1 text-sm text-muted">Katalog produk yang dipakai form penjualan dan stok.</p>
            </div>
            <button type="button" class="btn" @click="openCreate">
                <Icon name="plus" :size="16" />
                Tambah produk
            </button>
        </header>

        <section class="mt-6 rounded-xl border border-line bg-surface">
            <div class="border-b border-line p-4">
                <label class="mb-1 block text-xs text-muted" for="product-search">Cari produk</label>
                <div class="relative max-w-sm">
                    <span class="pointer-events-none absolute left-3 top-2.5 text-muted"><Icon name="search" :size="16" /></span>
                    <input id="product-search" v-model="search" type="search" class="field pl-9" placeholder="Nama produk" />
                </div>
            </div>

            <div v-if="products.length" class="overflow-x-auto">
                <table class="w-full border-collapse">
                    <thead>
                        <tr class="border-b border-line">
                            <th class="th">SKU</th>
                            <th class="th">Produk</th>
                            <th class="th">Kategori</th>
                            <th class="th">Satuan</th>
                            <th class="th text-right">Harga jual</th>
                            <th class="th text-right">Terjual</th>
                            <th class="th">Status</th>
                            <th class="th text-right">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="product in products"
                            :key="product.id"
                            class="border-b border-dashed border-line last:border-0 hover:bg-surface-2"
                        >
                            <td class="td numeric text-xs text-muted">{{ product.sku ?? '-' }}</td>
                            <td class="td">{{ product.name }}</td>
                            <td class="td text-xs text-muted">{{ product.category ?? 'Belum diisi' }}</td>
                            <td class="td text-xs">{{ product.unit }}</td>
                            <td class="td numeric text-right">{{ formatCurrency(product.sell_price) }}</td>
                            <td class="td numeric text-right text-xs text-muted">{{ formatNumber(product.sold_quantity) }}</td>
                            <td class="td">
                                <span
                                    class="rounded-md px-2 py-0.5 text-xs font-medium"
                                    :class="product.is_active ? 'bg-primary-soft text-primary' : 'bg-surface-2 text-muted'"
                                >
                                    {{ product.is_active ? 'Aktif' : 'Nonaktif' }}
                                </span>
                            </td>
                            <td class="td text-right">
                                <button type="button" class="text-xs font-medium text-primary hover:underline" @click="openEdit(product)">
                                    Ubah
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-else class="px-4 py-12 text-center text-sm text-muted">
                Tidak ada produk yang cocok. Ubah kata kunci atau tambah produk baru.
            </div>
        </section>

        <Modal
            :open="showForm"
            :title="editing ? 'Ubah produk' : 'Tambah produk'"
            description="Harga jual dipakai untuk menghitung nilai transaksi manual."
            @close="showForm = false"
        >
            <form class="space-y-4" @submit.prevent="submit">
                <div>
                    <label class="mb-1 block text-xs text-muted" for="product-name">Nama</label>
                    <input id="product-name" v-model="form.name" type="text" class="field" maxlength="255" />
                    <p v-if="form.errors.name" class="mt-1 text-xs text-danger">{{ form.errors.name }}</p>
                </div>

                <div class="grid gap-3 sm:grid-cols-2">
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="product-sku">SKU (opsional)</label>
                        <input id="product-sku" v-model="form.sku" type="text" class="field" maxlength="32" />
                        <p v-if="form.errors.sku" class="mt-1 text-xs text-danger">{{ form.errors.sku }}</p>
                    </div>
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="product-category">Kategori (opsional)</label>
                        <input id="product-category" v-model="form.category" type="text" class="field" maxlength="48" />
                        <p v-if="form.errors.category" class="mt-1 text-xs text-danger">{{ form.errors.category }}</p>
                    </div>
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="product-unit">Satuan</label>
                        <input id="product-unit" v-model="form.unit" type="text" class="field" maxlength="16" />
                        <p v-if="form.errors.unit" class="mt-1 text-xs text-danger">{{ form.errors.unit }}</p>
                    </div>
                    <div>
                        <label class="mb-1 block text-xs text-muted" for="product-price">Harga jual (Rp)</label>
                        <input id="product-price" v-model="form.sell_price" type="number" min="0" step="100" class="field" />
                        <p v-if="form.errors.sell_price" class="mt-1 text-xs text-danger">{{ form.errors.sell_price }}</p>
                    </div>
                </div>

                <label class="flex items-center gap-2 text-sm text-ink">
                    <input v-model="form.is_active" type="checkbox" class="h-4 w-4 rounded border-line" />
                    Aktif dan bisa dipilih pada form penjualan
                </label>

                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <button type="button" class="btn-quiet" @click="showForm = false">Batal</button>
                    <button type="submit" class="btn" :disabled="form.processing">
                        {{ editing ? 'Simpan perubahan' : 'Tambah produk' }}
                    </button>
                </div>
            </form>
        </Modal>
    </AppLayout>
</template>
