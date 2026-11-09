<script setup>
import { Head, Link, useForm } from '@inertiajs/vue3';
import { Button } from '@/Components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/Components/ui/card';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';

const form = useForm({
    name: '',
    email: '',
    password: '',
    password_confirmation: '',
});

function submit(event) {
    event.preventDefault();
    form.post('/register', {
        preserveScroll: true,
    });
}
</script>

<template>
    <Head title="Daftar" />

    <section class="flex min-h-screen items-center justify-center bg-canvas px-4 py-12 sm:px-6 lg:py-24">
        <Card class="w-full max-w-md shadow-sm">
            <CardHeader class="items-center text-center">
                <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
                    <span class="h-2.5 w-2.5 rounded-sm bg-brand-ink" aria-hidden="true"></span>
                </div>
                <CardTitle class="mt-4 text-2xl">Buat akun baru</CardTitle>
                <CardDescription class="text-sm">
                    Daftar untuk mulai mengelola inventaris toko Anda.
                </CardDescription>
            </CardHeader>

            <CardContent>
                <form class="space-y-5" @submit.prevent="submit">
                    <div>
                        <Label for="name" class="mb-1 text-sm text-ink">Nama lengkap</Label>
                        <Input
                            id="name"
                            name="name"
                            type="text"
                            v-model="form.name"
                            placeholder="Contoh: Budi Santoso"
                            :class="{ 'border-danger': form.errors.name }"
                            required
                            autocomplete="name"
                        />
                        <p v-if="form.errors.name" class="mt-1 text-sm text-danger">{{ form.errors.name }}</p>
                    </div>

                    <div>
                        <Label for="email" class="mb-1 text-sm text-ink">Email</Label>
                        <Input
                            id="email"
                            name="email"
                            type="email"
                            v-model="form.email"
                            placeholder="nama@contoh.com"
                            :class="{ 'border-danger': form.errors.email }"
                            required
                            autocomplete="username"
                        />
                        <p v-if="form.errors.email" class="mt-1 text-sm text-danger">{{ form.errors.email }}</p>
                    </div>

                    <div>
                        <Label for="password" class="mb-1 text-sm text-ink">Kata sandi</Label>
                        <Input
                            id="password"
                            name="password"
                            type="password"
                            v-model="form.password"
                            placeholder="••••••••"
                            :class="{ 'border-danger': form.errors.password }"
                            required
                            autocomplete="new-password"
                        />
                        <p v-if="form.errors.password" class="mt-1 text-sm text-danger">{{ form.errors.password }}</p>
                    </div>

                    <div>
                        <Label for="password_confirmation" class="mb-1 text-sm text-ink">Konfirmasi kata sandi</Label>
                        <Input
                            id="password_confirmation"
                            name="password_confirmation"
                            type="password"
                            v-model="form.password_confirmation"
                            placeholder="••••••••"
                            :class="{ 'border-danger': form.errors.password_confirmation }"
                            required
                            autocomplete="new-password"
                        />
                        <p v-if="form.errors.password_confirmation" class="mt-1 text-sm text-danger">
                            {{ form.errors.password_confirmation }}
                        </p>
                    </div>

                    <div v-if="form.errors.server" class="rounded-lg border border-danger bg-danger-soft p-4 text-sm text-danger">
                        {{ form.errors.server }}
                    </div>

                    <Button type="submit" class="w-full" :disabled="form.processing">
                        {{ form.processing ? 'Membuat akun...' : 'Daftar' }}
                    </Button>
                </form>

                <p class="mt-6 text-center text-sm text-muted">
                    Sudah memiliki akun?
                    <Link href="/login" class="font-medium text-primary hover:underline">
                        Masuk di sini
                    </Link>
                </p>
            </CardContent>
        </Card>
    </section>
</template>
