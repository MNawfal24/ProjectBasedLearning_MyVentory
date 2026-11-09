<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <div :class="cn('flex flex-col gap-1 pr-8 text-left', props.class)">
        <slot />
    </div>
</template>
