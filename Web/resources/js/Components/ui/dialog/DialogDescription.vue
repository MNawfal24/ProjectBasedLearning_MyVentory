<script setup>
import { DialogDescription } from 'reka-ui';
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <DialogDescription :class="cn('text-xs leading-relaxed text-muted', props.class)">
        <slot />
    </DialogDescription>
</template>
