<script setup>
defineProps({
    title: { type: String, required: true },
    hint: { type: String, default: '' },
});
</script>

<template>
    <section class="rounded-xl border border-line bg-surface">
        <header class="flex flex-wrap items-start justify-between gap-3 border-b border-line px-5 py-4">
            <div>
                <h2 class="text-sm font-semibold text-ink">{{ title }}</h2>
                <p v-if="hint" class="mt-1 text-xs leading-relaxed text-muted">{{ hint }}</p>
            </div>
            <slot name="action" />
        </header>
        <div class="px-5 py-4">
            <slot />
        </div>
    </section>
</template>
