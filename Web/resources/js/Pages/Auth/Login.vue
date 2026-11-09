<script setup>
import { Head, Link, useForm } from '@inertiajs/vue3';

const form = useForm({
    email: '',
    password: '',
    remember: false,
});

function submit(event) {
    event.preventDefault();
    form.post('/login', {
        preserveScroll: true,
    });
}
</script>

<template>
    <Head title="Masuk" />

    <section class="min-h-screen flex items-center justify-center bg-canvas px-4 py-12 sm:px-6 lg:py-24">
        <div class="max-w-md w-full space-y-8 bg-surface p-8 rounded-xl border border-line shadow-sm">
            <div class="mx-auto max-w-sm text-center">
                <div class="flex justify-center">
                    <div class="h-12 w-12 rounded-lg bg-primary flex items-center justify-center">
                        <span class="h-2.5 w-2.5 rounded-sm bg-brand-ink" aria-hidden="true"></span>
                    </div>
                </div>
                <h2 class="mt-6 text-2xl font-bold tracking-tight">Masuk ke MyVentory</h2>
                <p class="mt-2 text-muted">
                    Selamat kembali. Masuk untuk mengelola inventaris toko Anda.
                </p>
            </div>

            <form class="mt-8 space-y-6" @submit.prevent="submit">
                <div>
                    <label for="email" class="block text-sm font-medium text-ink">Email</label>
                    <div class="mt-1">
                        <input
                            id="email"
                            name="email"
                            type="email"
                            v-model="form.email"
                            class="field"
                            placeholder="nama@contoh.com"
                            :class="{ 'border-danger': form.errors.email }"
                            required
                            autocomplete="username"
                        />
                        <p v-if="form.errors.email" class="mt-1 text-sm text-danger">{{ form.errors.email }}</p>
                    </div>
                </div>

                <div>
                    <div class="flex items-center justify-between">
                        <label for="password" class="block text-sm font-medium text-ink">Kata sandi</label>
                    </div>
                    <div class="mt-1 relative">
                        <input
                            id="password"
                            name="password"
                            type="password"
                            v-model="form.password"
                            class="field pr-10"
                            placeholder="••••••••"
                            :class="{ 'border-danger': form.errors.password }"
                            required
                            autocomplete="current-password"
                        />
                        <p v-if="form.errors.password" class="mt-1 text-sm text-danger">{{ form.errors.password }}</p>
                    </div>
                </div>

                <div class="flex items-center">
                    <input
                        id="remember"
                        name="remember"
                        type="checkbox"
                        v-model="form.remember"
                        class="h-4 w-4 rounded border-line text-primary"
                    />
                    <label for="remember" class="ml-2 block text-sm text-muted">Ingat saya</label>
                </div>

                <div v-if="form.errors.server" class="bg-danger-soft border border-danger rounded-lg p-4 text-danger text-sm">
                    {{ form.errors.server }}
                </div>

                <div class="flex items-center justify-between">
                    <button
                        type="submit"
                        class="btn flex-1"
                        :disabled="form.processing"
                    >
                        {{ form.processing ? 'Memproses...' : 'Masuk' }}
                    </button>
                </div>
            </form>

            <p class="mt-8 text-center text-sm text-muted">
                Belum memiliki akun?
                <Link href="/register" class="font-medium text-primary hover:underline">
                    Buat akun baru
                </Link>
            </p>
            <p class="text-center text-xs text-muted">
                Demo: admin@myventory.com / admin123
            </p>
        </div>
    </section>
</template>
