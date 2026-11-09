<script setup>
import { cn } from '@/lib/utils';
import { buttonVariants } from './index.js';

const props = defineProps({
    variant: { type: String, default: 'default' },
    size: { type: String, default: 'default' },
    type: { type: String, default: 'button' },
    class: { type: null, default: '' },
});
</script>

<template>
    <button :type="props.type" :class="cn(buttonVariants({ variant: props.variant, size: props.size }), props.class)">
        <slot />
    </button>
</template>
