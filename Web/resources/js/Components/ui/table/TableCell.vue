<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <td :class="cn('px-4 py-3 align-middle', props.class)">
        <slot />
    </td>
</template>
