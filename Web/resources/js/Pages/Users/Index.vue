<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import { ref } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';
import { Label } from '@/Components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/Components/ui/table';
import AppLayout from '../../Layouts/AppLayout.vue';
import Icon from '../../Components/Icon.vue';
import Modal from '../../Components/Modal.vue';
import PageHeader from '../../Components/PageHeader.vue';
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
        <PageHeader
            title="Akun"
            description="Akun staf untuk aplikasi mobile. Akun ini hanya bisa membaca data; semua perubahan dilakukan dari dashboard."
        >
            <template #actions>
                <Button @click="openCreate">
                    <Icon name="plus" :size="16" />
                    Tambah akun mobile
                </Button>
            </template>
        </PageHeader>

        <section class="panel mt-8">
            <template v-if="users.length">
                <ul class="divide-y divide-line md:hidden">
                    <li v-for="user in users" :key="user.id" class="px-4 py-3">
                        <div class="flex items-baseline justify-between gap-3">
                            <span class="truncate text-body text-ink">{{ user.name }}</span>
                            <Badge :variant="user.role === 'admin' ? 'default' : 'secondary'" class="shrink-0">
                                {{ user.role === 'admin' ? 'Admin' : 'Mobile' }}
                            </Badge>
                        </div>
                        <p class="mt-0.5 truncate text-2xs text-muted">{{ user.email }}</p>
                        <div class="mt-1.5 flex items-baseline justify-between gap-3">
                            <span class="text-2xs text-muted">Dibuat {{ formatDateTime(user.created_at) }}</span>
                            <button type="button" class="link-inline text-xs" @click="openReset(user)">Ubah sandi</button>
                        </div>
                    </li>
                </ul>

                <div class="hidden md:block">
                <Table>
                    <TableHeader>
                        <TableRow class="table-head-row hover:bg-surface-2">
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
                                <button type="button" class="link-inline text-xs" @click="openReset(user)">
                                    Ubah sandi
                                </button>
                            </TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
                </div>
            </template>

            <div v-else class="px-5 py-14 text-center">
                <p class="text-body text-muted">Belum ada akun. Tambah satu untuk memberi akses aplikasi mobile.</p>
            </div>
        </section>

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
