<script setup>
defineProps({
    title: { type: String, required: true },
    description: { type: String, default: '' },
    meta: { type: String, default: '' },
});
</script>

<template>
    <header class="page-head">
        <div class="min-w-0">
            <h1 class="page-title">{{ title }}</h1>
            <p v-if="description" class="page-sub">{{ description }}</p>
            <p v-if="meta" class="page-meta">{{ meta }}</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
            <slot name="actions" />
        </div>
    </header>
</template>