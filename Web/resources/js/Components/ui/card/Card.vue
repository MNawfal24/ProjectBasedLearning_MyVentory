<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <div :class="cn('rounded-panel border border-line bg-surface text-ink', props.class)">
        <slot />
    </div>
</template>