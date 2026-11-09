<script setup>
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/Components/ui/card';

defineProps({
    title: { type: String, required: true },
    hint: { type: String, default: '' },
});
</script>

<template>
    <Card>
        <CardHeader class="flex-row flex-wrap items-start justify-between gap-3 border-b border-line py-4">
            <div class="min-w-0">
                <CardTitle>{{ title }}</CardTitle>
                <CardDescription v-if="hint" class="mt-1">{{ hint }}</CardDescription>
            </div>
            <slot name="action" />
        </CardHeader>
        <CardContent>
            <slot />
        </CardContent>
    </Card>
</template>
