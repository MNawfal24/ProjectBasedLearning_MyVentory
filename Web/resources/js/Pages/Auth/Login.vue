<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { Button } from '@/Components/ui/button';
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

    <div class="grid min-h-screen bg-canvas lg:grid-cols-[1fr_30rem]">
        <div class="hidden flex-col justify-between border-r border-line bg-surface px-12 py-12 lg:flex">
            <div class="flex items-center gap-2.5 text-ink">
                <img src="/logo.png" alt="" class="h-8 w-8 rounded-md object-contain" />
                <span class="text-[15px] font-semibold tracking-tight">MyVentory</span>
            </div>
        </div>

        <main class="flex items-center justify-center px-4 py-12 sm:px-8">
            <div class="w-full max-w-sm">
                <div class="mb-8 flex items-center gap-2.5 lg:hidden">
                    <img src="/logo.png" alt="" class="h-8 w-8 rounded-md object-contain" />
                    <span class="text-[15px] font-semibold tracking-tight">MyVentory</span>
                </div>

                <h1 class="text-2xl font-semibold tracking-tight text-ink">Masuk</h1>
                <p class="mt-1.5 text-body text-muted">Gunakan akun yang dibuat admin untuk dashboard ini.</p>

                <form class="mt-8 space-y-4" @submit.prevent="submit">
                    <div>
                        <Label for="email" class="mb-1">Email</Label>
                        <Input
                            id="email"
                            name="email"
                            type="email"
                            v-model="form.email"
                            :class="{ 'border-danger': form.errors.email }"
                            autocomplete="username"
                        />
                        <p v-if="form.errors.email" class="mt-1 text-xs text-danger">{{ form.errors.email }}</p>
                    </div>

                    <div>
                        <Label for="password" class="mb-1">Kata sandi</Label>
                        <Input
                            id="password"
                            name="password"
                            type="password"
                            v-model="form.password"
                            :class="{ 'border-danger': form.errors.password }"
                            autocomplete="current-password"
                        />
                        <p v-if="form.errors.password" class="mt-1 text-xs text-danger">{{ form.errors.password }}</p>
                    </div>

                    <Label class="flex items-center gap-2 text-xs text-muted">
                        <input v-model="form.remember" type="checkbox" class="h-4 w-4 rounded border-line text-primary" />
                        Ingat saya
                    </Label>

                    <div v-if="form.errors.server" class="rounded-lg border border-danger bg-danger-soft p-3 text-xs text-danger">
                        {{ form.errors.server }}
                    </div>

                    <Button type="submit" class="h-10 w-full" :disabled="form.processing">
                        {{ form.processing ? 'Memproses...' : 'Masuk' }}
                    </Button>
                </form>

                <p class="mt-8 text-2xs leading-relaxed text-muted">
                    Akun demo dari seeder: admin@myventory.com / admin123
                </p>
            </div>
        </main>
    </div>
</template>