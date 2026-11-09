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
                'border-b border-dashed border-line transition-colors hover:bg-surface-2 data-[state=selected]:bg-surface-2',
                props.class,
            )
        "
    >
        <slot />
    </tr>
</template>
