<script setup>
import { computed } from 'vue';
import { Badge } from '@/Components/ui/badge';
import { Card, CardDescription, CardHeader, CardTitle } from '@/Components/ui/card';
import Icon from './Icon.vue';

const props = defineProps({
    items: { type: Array, required: true },
});

const cells = computed(() =>
    props.items.map((item) => {
        const change = item.change_pct;
        const positive = change !== null && change >= 0;

        return {
            ...item,
            positive,
            delta: change === null ? null : `${positive ? '+' : ''}${String(change).replace('.', ',')}%`,
        };
    }),
);
</script>

<template>
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card v-for="cell in cells" :key="cell.label">
            <CardHeader class="gap-2">
                <CardDescription>{{ cell.label }}</CardDescription>
                <div class="flex flex-wrap items-center justify-between gap-2">
                    <CardTitle class="numeric text-2xl">{{ cell.value }}</CardTitle>
                    <Badge v-if="cell.delta" :variant="cell.positive ? 'default' : 'destructive'" class="gap-1">
                        <Icon :name="cell.positive ? 'up' : 'down'" :size="12" />
                        <span class="numeric">{{ cell.delta }}</span>
                    </Badge>
                </div>
                <p class="text-xs text-muted">{{ cell.compare }}</p>
            </CardHeader>
        </Card>
    </div>
</template>
