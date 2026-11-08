<script setup>
import { Head, Link } from '@inertiajs/vue3';

const stats = $props.stats;
</script>

<template>
    <Head title="Beranda" />

    <section class="min-h-screen flex flex-col bg-canvas text-ink">
        <nav class="border-b border-line bg-surface/50">
            <div class="mx-auto max-w-[1400px] px-4 py-3 flex items-center justify-between sm:px-6 lg:px-8">
                <Link href="/" class="flex items-center gap-2 text-xl font-semibold tracking-tight">
                    <span class="h-2.5 w-2.5 rounded-sm bg-primary" aria-hidden="true"></span>
                    MyVentory
                </Link>
                <div class="flex items-center gap-3">
                    <Link href="/login" class="btn-quiet">Masuk</Link>
                    <Link href="/register" class="btn">Daftar</Link>
                </div>
            </div>
        </nav>

        <main class="flex-1">
            <div class="mx-auto max-w-[1400px] px-4 py-12 sm:px-6 lg:px-8 lg:py-20">
                <div class="text-center max-w-2xl mx-auto">
                    <h1 class="text-4xl font-bold tracking-tight sm:text-5xl">
                        Kelola stok dan penjualan<br />
                        <span class="text-primary">secara nyata.</span>
                    </h1>
                    <p class="mt-4 text-lg text-muted max-w-lg mx-auto">
                        MyVentory membantu UMKM mencatat stok, mencatat transaksi, dan memantau
                        lapenjualan melalui database PostgreSQL yang terintegrasi dengan aplikasi Flutter.
                    </p>
                    <div class="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
                        <Link href="/login" class="btn flex-1 sm:flex-none">Mulai masuk</Link>
                        <Link href="/register" class="btn-quiet flex-1 sm:flex-none">Buat akun baru</Link>
                    </div>
                </div>

                <div class="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
                    <div class="rounded-lg border border-line bg-surface p-6">
                        <div class="w-10 h-10 rounded-lg bg-primary-soft flex items-center justify-center text-primary mb-4">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                            </svg>
                        </div>
                        <h3 class="text-lg font-semibold">Stok terpantau</h3>
                        <p class="mt-2 text-sm text-muted">
                            Saldo stok per outlet dan produk, dengan peringatan ketika stok menipis.
                        </p>
                    </div>

                    <div class="rounded-lg border border-line bg-surface p-6">
                        <div class="w-10 h-10 rounded-lg bg-primary-soft flex items-center justify-center text-primary mb-4">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <h3 class="text-lg font-semibold">Transaksi tercatat</h3>
                        <p class="mt-2 text-sm text-muted">
                            Setiap struk penjualan tersimpan dengan detail item, metode pembayaran, dan waktu.
                        </p>
                    </div>

                    <div class="rounded-lg border border-line bg-surface p-6">
                        <div class="w-10 h-10 rounded-lg bg-primary-soft flex items-center justify-center text-primary mb-4">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <h3 class="text-lg font-semibold">Laporan penjualan</h3>
                        <p class="mt-2 text-sm text-muted">
                            Ringkasan pendapatan, transaksi, dan produk terlaris dalam satu dashboard.
                        </p>
                    </div>
                </div>

                <div class="mt-16 rounded-xl border border-line bg-surface-2 p-8 text-center">
                    <h3 class="text-xl font-semibold">Siap mulai?</h3>
                    <p class="mt-2 text-muted">Buat akun dan kelola inventaris toko Anda.</p>
                    <div class="mt-6">
                        <Link href="/register" class="btn">Daftar sekarang</Link>
                    </div>
                </div>
            </div>
        </main>

        <footer class="border-t border-line bg-surface py-8">
            <div class="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8">
                <p class="text-xs text-muted">MyVentory · Smart Inventory for UMKM</p>
            </div>
        </footer>
    </section>
</template>
