<script setup>
import { computed } from 'vue';
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
            <button
                type="button"
                class="btn-quiet px-3 py-1.5 text-xs"
                :disabled="current <= 1"
                @click="visitWith({ page: current - 1 })"
            >
                Sebelumnya
            </button>
            <button
                type="button"
                class="btn-quiet px-3 py-1.5 text-xs"
                :disabled="current >= last"
                @click="visitWith({ page: current + 1 })"
            >
                Berikutnya
            </button>
        </div>
    </div>
</template>
