<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { Button } from '@/Components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/Components/ui/card';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';

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

    <section class="flex min-h-screen items-center justify-center bg-canvas px-4 py-12 sm:px-6 lg:py-24">
        <Card class="w-full max-w-md shadow-sm">
            <CardHeader class="items-center text-center">
                <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
                    <span class="h-2.5 w-2.5 rounded-sm bg-brand-ink" aria-hidden="true"></span>
                </div>
                <CardTitle class="mt-4 text-2xl">Masuk ke MyVentory</CardTitle>
                <CardDescription class="text-sm">
                    Selamat kembali. Masuk untuk mengelola inventaris toko Anda.
                </CardDescription>
            </CardHeader>

            <CardContent>
                <form class="space-y-5" @submit.prevent="submit">
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
                            autocomplete="current-password"
                        />
                        <p v-if="form.errors.password" class="mt-1 text-sm text-danger">{{ form.errors.password }}</p>
                    </div>

                    <Label class="flex items-center gap-2 text-sm text-muted">
                        <input v-model="form.remember" type="checkbox" class="h-4 w-4 rounded border-line text-primary" />
                        Ingat saya
                    </Label>

                    <div v-if="form.errors.server" class="rounded-lg border border-danger bg-danger-soft p-4 text-sm text-danger">
                        {{ form.errors.server }}
                    </div>

                    <Button type="submit" class="w-full" :disabled="form.processing">
                        {{ form.processing ? 'Memproses...' : 'Masuk' }}
                    </Button>
                </form>

                <p class="mt-6 text-center text-xs text-muted">
                    Akun staf mobile dibuat oleh admin dari menu Akun. Demo: admin@myventory.com / admin123
                </p>
            </CardContent>
        </Card>
    </section>
</template>
