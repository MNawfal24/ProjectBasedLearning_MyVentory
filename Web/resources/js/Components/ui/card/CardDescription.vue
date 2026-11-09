<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <p :class="cn('text-xs leading-relaxed text-muted', props.class)">
        <slot />
    </p>
</template>
