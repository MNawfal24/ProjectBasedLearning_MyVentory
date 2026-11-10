<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <label :class="cn('block text-2xs font-medium text-muted', props.class)">
        <slot />
    </label>
</template>