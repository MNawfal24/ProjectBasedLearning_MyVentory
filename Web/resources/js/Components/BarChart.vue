<script setup>
import { computed } from 'vue';
import { formatCompact } from '../format';

const props = defineProps({
    items: { type: Array, required: true },
    height: { type: Number, default: 150 },
});

const max = computed(() => Math.max(1, ...props.items.map((item) => item.value)));
const peak = computed(() => props.items.reduce((best, item) => (item.value > (best?.value ?? -1) ? item : best), null));

// Twenty-four hour labels do not fit side by side, so only every third one is
// drawn once the row gets crowded.
const labelStep = computed(() => (props.items.length > 12 ? 3 : 1));
</script>

<template>
    <div>
        <div v-if="items.length === 0" class="flex h-36 items-center justify-center text-sm text-muted">
            Belum ada data.
        </div>

        <div v-else>
            <div class="flex items-end gap-1.5" :style="{ height: `${height}px` }">
                <div v-for="item in items" :key="item.label" class="flex h-full flex-1 flex-col justify-end">
                    <!-- A zero bar stays absent: a 2px stub would read as a dashed baseline. -->
                    <div
                        v-if="item.value > 0"
                        class="w-full rounded-t-sm transition-colors"
                        :class="item === peak ? 'bg-primary' : 'bg-primary/35'"
                        :style="{ height: `${Math.max(2, (item.value / max) * 100)}%` }"
                        :title="`${item.label}: ${formatCompact(item.value)}`"
                    ></div>
                </div>
            </div>
            <div class="mt-2 flex gap-1.5">
                <span
                    v-for="(item, index) in items"
                    :key="`label-${item.label}`"
                    class="flex-1 whitespace-nowrap text-center text-[10px] leading-none text-muted"
                >
                    {{ index % labelStep === 0 ? item.label : '' }}
                </span>
            </div>
        </div>
    </div>
</template>
