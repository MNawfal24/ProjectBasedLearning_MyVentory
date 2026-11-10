<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});
</script>

<template>
    <tr
        :class="
            cn(
                'border-b border-line transition-colors last:border-0 hover:bg-surface-2',
                props.class,
            )
        "
    >
        <slot />
    </tr>
</template>