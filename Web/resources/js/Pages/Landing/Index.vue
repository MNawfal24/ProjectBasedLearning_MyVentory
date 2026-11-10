<script setup>
import { Head, Link } from '@inertiajs/vue3';
import Icon from '../../Components/Icon.vue';

/*
 * Only reachable surfaces are named here. There is no public signup: staff
 * accounts are created by an admin, so the page offers one action, sign in.
 */
const surfaces = [
    { icon: 'overview', label: 'Ringkasan penjualan', detail: 'Pendapatan, jumlah struk, dan jam tersibuk dari data kasir.' },
    { icon: 'stock', label: 'Saldo stok', detail: 'Saldo per outlet dan produk, dengan penanda stok menipis dan habis.' },
    { icon: 'receipt', label: 'Riwayat transaksi', detail: 'Setiap struk beserta item, metode pembayaran, dan waktunya.' },
];
</script>

<template>
    <Head title="Beranda" />

    <div class="flex min-h-screen flex-col bg-canvas text-ink">
        <header class="border-b border-line bg-surface">
            <div class="mx-auto flex max-w-[1100px] items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
                <span class="flex items-center gap-2.5">
                    <img src="/logo.png" alt="" class="h-8 w-8 rounded-md object-contain" />
                    <span class="text-[15px] font-semibold tracking-tight">MyVentory</span>
                </span>
                <Link href="/login" class="btn-quiet">Masuk</Link>
            </div>
        </header>

        <main class="mx-auto w-full max-w-[1100px] flex-1 px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
            <div class="grid gap-12 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
                <div>
                    <h1 class="max-w-md text-3xl font-semibold tracking-tight sm:text-4xl">
                        Back office untuk stok dan penjualan toko.
                    </h1>
                    <p class="mt-4 max-w-md text-body leading-relaxed text-muted">
                        MyVentory membaca database yang sama dengan aplikasi kasir. Angka di dashboard adalah
                        hasil penjumlahan baris transaksi dan pergerakan stok, bukan perkiraan.
                    </p>
                    <Link href="/login" class="btn mt-8">Masuk ke dashboard</Link>
                    <p class="mt-4 text-2xs text-muted">Akun staf dibuat oleh admin, tidak ada pendaftaran mandiri.</p>
                </div>

                <dl class="divide-y divide-line border-y border-line">
                    <div v-for="surface in surfaces" :key="surface.label" class="flex gap-4 py-5">
                        <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary-soft text-primary">
                            <Icon :name="surface.icon" :size="17" />
                        </span>
                        <div class="min-w-0">
                            <dt class="text-body font-medium text-ink">{{ surface.label }}</dt>
                            <dd class="mt-0.5 text-xs leading-relaxed text-muted">{{ surface.detail }}</dd>
                        </div>
                    </div>
                </dl>
            </div>
        </main>

        <footer class="border-t border-line bg-surface">
            <div class="mx-auto max-w-[1100px] px-4 py-6 text-2xs text-muted sm:px-6 lg:px-8">
                MyVentory &middot; Smart inventory untuk UMKM
            </div>
        </footer>
    </div>
</template>