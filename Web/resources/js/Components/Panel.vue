<script setup>
defineProps({
    title: { type: String, required: true },
    hint: { type: String, default: '' },
});
</script>

<template>
    <section class="panel flex flex-col">
        <header class="panel-head">
            <div class="min-w-0">
                <h2 class="panel-title">{{ title }}</h2>
                <p v-if="hint" class="panel-hint">{{ hint }}</p>
            </div>
            <slot name="action" />
        </header>
        <div class="panel-body flex-1">
            <slot />
        </div>
    </section>
</template>