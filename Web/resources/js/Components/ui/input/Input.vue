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
                'flex h-9 w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink shadow-xs transition-colors placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-50',
                props.class,
            )
        "
    />
</template>
