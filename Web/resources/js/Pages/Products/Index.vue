<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { ref, watch } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/Components/ui/table';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import PageHeader from '../../Components/PageHeader.vue';
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
        <PageHeader title="Products" description="Katalog produk yang dipakai form penjualan dan stok.">
            <template #actions>
                <Button @click="openCreate">
                    <Icon name="plus" :size="16" />
                    Tambah produk
                </Button>
            </template>
        </PageHeader>

        <section class="panel mt-8">
            <div class="border-b border-line px-5 py-4">
                <Label for="product-search" class="mb-1">Cari produk</Label>
                <div class="relative max-w-sm">
                    <span class="pointer-events-none absolute left-3 top-2.5 text-muted"><Icon name="search" :size="16" /></span>
                    <Input id="product-search" v-model="search" type="search" class="pl-9" placeholder="Nama produk" />
                </div>
            </div>

            <template v-if="products.length">
                <ul class="divide-y divide-line md:hidden">
                    <li v-for="product in products" :key="product.id" class="px-4 py-3">
                        <div class="flex items-baseline justify-between gap-3">
                            <span class="truncate text-body text-ink">{{ product.name }}</span>
                            <span class="numeric shrink-0 text-body text-ink">{{ formatCurrency(product.sell_price) }}</span>
                        </div>
                        <div class="mt-1.5 flex items-center justify-between gap-3">
                            <p class="text-2xs text-muted">
                                {{ product.sku ?? 'tanpa SKU' }} &middot; {{ formatNumber(product.sold_quantity) }} terjual
                            </p>
                            <button type="button" class="link-inline text-xs" @click="openEdit(product)">Ubah</button>
                        </div>
                    </li>
                </ul>

                <div class="hidden md:block">
                <Table>
                    <TableHeader>
                        <TableRow class="table-head-row hover:bg-surface-2">
                            <TableHead>SKU</TableHead>
                            <TableHead>Produk</TableHead>
                            <TableHead>Kategori</TableHead>
                            <TableHead>Satuan</TableHead>
                            <TableHead class="text-right">Harga jual</TableHead>
                            <TableHead class="text-right">Terjual</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead class="text-right">Aksi</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow v-for="product in products" :key="product.id">
                            <TableCell class="numeric text-xs text-muted">{{ product.sku ?? '-' }}</TableCell>
                            <TableCell>{{ product.name }}</TableCell>
                            <TableCell class="text-xs text-muted">{{ product.category ?? 'Belum diisi' }}</TableCell>
                            <TableCell class="text-xs">{{ product.unit }}</TableCell>
                            <TableCell class="numeric text-right">{{ formatCurrency(product.sell_price) }}</TableCell>
                            <TableCell class="numeric text-right text-xs text-muted">{{ formatNumber(product.sold_quantity) }}</TableCell>
                            <TableCell>
                                <Badge :variant="product.is_active ? 'default' : 'secondary'">
                                    {{ product.is_active ? 'Aktif' : 'Nonaktif' }}
                                </Badge>
                            </TableCell>
                            <TableCell class="text-right">
                                <Button variant="link" size="sm" class="h-auto p-0" @click="openEdit(product)">Ubah</Button>
                            </TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
                </div>
            </template>

            <div v-else class="px-5 py-14 text-center">
                <p class="text-body text-muted">Tidak ada produk yang cocok. Ubah kata kunci atau tambah produk baru.</p>
                <Button v-if="filters.search" variant="outline" class="mt-3" @click="search = ''">Hapus pencarian</Button>
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
                    <Label for="product-name" class="mb-1">Nama</Label>
                    <Input id="product-name" v-model="form.name" type="text" maxlength="255" />
                    <p v-if="form.errors.name" class="mt-1 text-xs text-danger">{{ form.errors.name }}</p>
                </div>

                <div class="grid gap-3 sm:grid-cols-2">
                    <div>
                        <Label for="product-sku" class="mb-1">SKU (opsional)</Label>
                        <Input id="product-sku" v-model="form.sku" type="text" maxlength="32" />
                        <p v-if="form.errors.sku" class="mt-1 text-xs text-danger">{{ form.errors.sku }}</p>
                    </div>
                    <div>
                        <Label for="product-category" class="mb-1">Kategori (opsional)</Label>
                        <Input id="product-category" v-model="form.category" type="text" maxlength="48" />
                        <p v-if="form.errors.category" class="mt-1 text-xs text-danger">{{ form.errors.category }}</p>
                    </div>
                    <div>
                        <Label for="product-unit" class="mb-1">Satuan</Label>
                        <Input id="product-unit" v-model="form.unit" type="text" maxlength="16" />
                        <p v-if="form.errors.unit" class="mt-1 text-xs text-danger">{{ form.errors.unit }}</p>
                    </div>
                    <div>
                        <Label for="product-price" class="mb-1">Harga jual (Rp)</Label>
                        <Input id="product-price" v-model="form.sell_price" type="number" min="0" step="100" />
                        <p v-if="form.errors.sell_price" class="mt-1 text-xs text-danger">{{ form.errors.sell_price }}</p>
                    </div>
                </div>

                <Label class="flex items-center gap-2 text-sm text-ink">
                    <input v-model="form.is_active" type="checkbox" class="h-4 w-4 rounded border-line" />
                    Aktif dan bisa dipilih pada form penjualan
                </Label>

                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <Button variant="outline" @click="showForm = false">Batal</Button>
                    <Button type="submit" :disabled="form.processing">
                        {{ editing ? 'Simpan perubahan' : 'Tambah produk' }}
                    </Button>
                </div>
            </form>
        </Modal>
    </AppLayout>
</template>
