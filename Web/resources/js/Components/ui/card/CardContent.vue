<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <div :class="cn('px-5 py-4', props.class)">
        <slot />
    </div>
</template>
