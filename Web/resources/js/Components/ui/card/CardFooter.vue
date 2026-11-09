<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <div :class="cn('flex items-center gap-2 border-t border-line px-5 py-4', props.class)">
        <slot />
    </div>
</template>
