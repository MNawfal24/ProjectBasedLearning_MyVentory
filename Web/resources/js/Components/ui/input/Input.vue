<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
    class: { type: null, default: '' },
});

const model = defineModel({ type: [String, Number], default: '' });
</script>

<template>
    <input
        v-model="model"
        :class="
            cn(
                'flex h-11 w-full rounded-lg border border-line bg-surface px-3 py-2 text-body text-ink transition-colors sm:h-9 placeholder:text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/25 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50',
                props.class,
            )
        "
    />
</template>