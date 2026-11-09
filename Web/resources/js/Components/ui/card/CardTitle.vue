<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <h3 :class="cn('text-sm font-semibold leading-none tracking-tight text-ink', props.class)">
        <slot />
    </h3>
</template>
