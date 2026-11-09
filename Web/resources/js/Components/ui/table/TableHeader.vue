<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <thead :class="cn('[&_tr]:border-b [&_tr]:border-line', props.class)">
        <slot />
    </thead>
</template>
