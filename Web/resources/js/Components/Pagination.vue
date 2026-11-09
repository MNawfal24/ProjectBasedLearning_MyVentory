<script setup>
import { computed } from 'vue';
import { Button } from '@/Components/ui/button';
import { visitWith } from '../ui';

const props = defineProps({
    paginator: { type: Object, required: true },
    label: { type: String, default: 'data' },
});

const current = computed(() => props.paginator.current_page);
const last = computed(() => props.paginator.last_page);
</script>

<template>
    <div v-if="last > 1" class="flex flex-wrap items-center justify-between gap-3 border-t border-line px-4 py-3">
        <p class="text-xs text-muted">
            Halaman {{ current }} dari {{ last }} · {{ paginator.total }} {{ label }}
        </p>
        <div class="flex gap-2">
            <Button variant="outline" size="sm" :disabled="current <= 1" @click="visitWith({ page: current - 1 })">
                Sebelumnya
            </Button>
            <Button variant="outline" size="sm" :disabled="current >= last" @click="visitWith({ page: current + 1 })">
                Berikutnya
            </Button>
        </div>
    </div>
</template>
