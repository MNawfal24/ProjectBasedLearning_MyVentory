<script setup>
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/Components/ui/dialog';
import Icon from './Icon.vue';

defineProps({
    open: { type: Boolean, default: false },
    title: { type: String, required: true },
    description: { type: String, default: '' },
});

const emit = defineEmits(['close']);
</script>

<template>
    <Dialog :open="open" @update:open="(value) => !value && emit('close')">
        <DialogContent>
            <DialogHeader>
                <DialogTitle>{{ title }}</DialogTitle>
                <DialogDescription v-if="description">{{ description }}</DialogDescription>
            </DialogHeader>

            <DialogClose
                class="absolute right-3 top-3 rounded-lg p-1.5 text-muted transition-colors hover:bg-surface-2 hover:text-ink"
                aria-label="Tutup"
            >
                <Icon name="close" :size="18" />
            </DialogClose>

            <slot />
        </DialogContent>
    </Dialog>
</template>
