<script setup>
import { DialogContent, DialogOverlay, DialogPortal } from 'reka-ui';
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <DialogPortal>
        <DialogOverlay class="fixed inset-0 z-40 bg-black/45" />
        <DialogContent
            :class="
                cn(
                    'fixed left-1/2 top-1/2 z-50 grid max-h-[92vh] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 gap-4 overflow-y-auto rounded-panel border border-line bg-surface p-6 shadow-raised focus:outline-none',
                    props.class,
                )
            "
        >
            <slot />
        </DialogContent>
    </DialogPortal>
</template>
