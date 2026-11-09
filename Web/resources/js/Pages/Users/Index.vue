<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { ref } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { Button } from '@/Components/ui/button';
import { Card, CardContent } from '@/Components/ui/card';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/Components/ui/table';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import { formatDateTime } from '../../format';

const props = defineProps({
    users: { type: Array, required: true },
});

const showForm = ref(false);
const resetting = ref(null);

const form = useForm({
    name: '',
    email: '',
    password: '',
});

const passwordForm = useForm({ password: '' });

function openCreate() {
    form.reset();
    form.clearErrors();
    showForm.value = true;
}

function submit() {
    form.post('/users', {
        preserveScroll: true,
        onSuccess: () => {
            showForm.value = false;
            form.reset();
        },
    });
}

function openReset(user) {
    resetting.value = user;
    passwordForm.reset();
    passwordForm.clearErrors();
}

function submitReset() {
    passwordForm.patch(`/users/${resetting.value.id}/password`, {
        preserveScroll: true,
        onSuccess: () => (resetting.value = null),
    });
}
</script>

<template>
    <Head title="Akun" />

    <AppLayout>
        <header class="flex flex-wrap items-end justify-between gap-4">
            <div>
                <h1 class="text-2xl font-semibold tracking-tight text-ink">Akun</h1>
                <p class="mt-1 text-sm text-muted">
                    Akun staf untuk aplikasi mobile. Akun ini hanya bisa membaca data; semua perubahan dilakukan dari dashboard.
                </p>
            </div>
            <Button @click="openCreate">
                <Icon name="plus" :size="16" />
                Tambah akun mobile
            </Button>
        </header>

        <Card class="mt-6">
            <template v-if="users.length">
                <Table>
                    <TableHeader>
                        <TableRow class="hover:bg-transparent">
                            <TableHead>Nama</TableHead>
                            <TableHead>Email</TableHead>
                            <TableHead>Peran</TableHead>
                            <TableHead>Dibuat</TableHead>
                            <TableHead class="text-right">Aksi</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow v-for="user in users" :key="user.id">
                            <TableCell>{{ user.name }}</TableCell>
                            <TableCell class="text-sm text-muted">{{ user.email }}</TableCell>
                            <TableCell>
                                <Badge :variant="user.role === 'admin' ? 'default' : 'secondary'">
                                    {{ user.role === 'admin' ? 'Admin' : 'Mobile' }}
                                </Badge>
                            </TableCell>
                            <TableCell class="numeric text-xs text-muted">{{ formatDateTime(user.created_at) }}</TableCell>
                            <TableCell class="text-right">
                                <Button variant="link" size="sm" class="h-auto p-0" @click="openReset(user)">
                                    Ubah sandi
                                </Button>
                            </TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </template>

            <div v-else class="px-4 py-12 text-center text-sm text-muted">
                Belum ada akun. Tambah satu untuk memberi akses aplikasi mobile.
            </div>
        </Card>

        <Modal
            :open="showForm"
            title="Tambah akun mobile"
            description="Akun ini memakai peran Mobile dan hanya dapat membaca data dari aplikasi."
            @close="showForm = false"
        >
            <form class="space-y-4" @submit.prevent="submit">
                <div>
                    <Label for="user-name" class="mb-1">Nama</Label>
                    <Input id="user-name" v-model="form.name" type="text" maxlength="255" />
                    <p v-if="form.errors.name" class="mt-1 text-xs text-danger">{{ form.errors.name }}</p>
                </div>

                <div>
                    <Label for="user-email" class="mb-1">Email</Label>
                    <Input id="user-email" v-model="form.email" type="email" maxlength="255" />
                    <p v-if="form.errors.email" class="mt-1 text-xs text-danger">{{ form.errors.email }}</p>
                </div>

                <div>
                    <Label for="user-password" class="mb-1">Kata sandi</Label>
                    <Input id="user-password" v-model="form.password" type="password" autocomplete="new-password" />
                    <p v-if="form.errors.password" class="mt-1 text-xs text-danger">{{ form.errors.password }}</p>
                </div>

                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <Button variant="outline" @click="showForm = false">Batal</Button>
                    <Button type="submit" :disabled="form.processing">Simpan</Button>
                </div>
            </form>
        </Modal>

        <Modal
            :open="resetting !== null"
            title="Ubah kata sandi"
            :description="resetting ? `Kata sandi baru untuk ${resetting.name}.` : ''"
            @close="resetting = null"
        >
            <form class="space-y-4" @submit.prevent="submitReset">
                <div>
                    <Label for="reset-password" class="mb-1">Kata sandi baru</Label>
                    <Input id="reset-password" v-model="passwordForm.password" type="password" autocomplete="new-password" />
                    <p v-if="passwordForm.errors.password" class="mt-1 text-xs text-danger">
                        {{ passwordForm.errors.password }}
                    </p>
                </div>

                <div class="flex justify-end gap-2 border-t border-line pt-3">
                    <Button variant="outline" @click="resetting = null">Batal</Button>
                    <Button type="submit" :disabled="passwordForm.processing">Simpan</Button>
                </div>
            </form>
        </Modal>
    </AppLayout>
</template>
