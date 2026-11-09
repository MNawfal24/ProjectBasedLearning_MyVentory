<script setup>
import { ProgressIndicator, ProgressRoot } from 'reka-ui';
import { cn } from '@/lib/utils';

const props = defineProps({
    modelValue: { type: Number, default: 0 },
    class: { type: null, default: '' },
});
</script>

<template>
    <ProgressRoot
        :model-value="props.modelValue"
        :class="cn('relative h-1.5 w-full overflow-hidden rounded-full bg-surface-2', props.class)"
    >
        <ProgressIndicator
            class="h-full w-full flex-1 rounded-full bg-primary transition-transform"
            :style="`transform: translateX(-${100 - (props.modelValue || 0)}%)`"
        />
    </ProgressRoot>
</template>
