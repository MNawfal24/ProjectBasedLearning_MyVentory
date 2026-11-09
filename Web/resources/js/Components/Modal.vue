<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';
import Icon from './Icon.vue';

const props = defineProps({
    open: { type: Boolean, default: false },
    title: { type: String, required: true },
    description: { type: String, default: '' },
});

const emit = defineEmits(['close']);
const panel = ref(null);

function onKeydown(event) {
    if (event.key === 'Escape' && props.open) {
        emit('close');
    }
}

watch(
    () => props.open,
    async (open) => {
        if (!open) {
            return;
        }
        await nextTick();
        panel.value?.querySelector('input, select, textarea, button')?.focus();
    },
);

document.addEventListener('keydown', onKeydown);
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown));
</script>

<template>
    <Teleport to="body">
        <div
            v-if="open"
            class="fixed inset-0 z-40 flex items-end justify-center bg-black/45 sm:items-center sm:p-4"
            @click.self="emit('close')"
        >
            <div
                ref="panel"
                role="dialog"
                aria-modal="true"
                :aria-label="title"
                class="max-h-[92vh] w-full overflow-y-auto rounded-t-xl border border-line bg-surface p-5 sm:max-w-lg sm:rounded-xl"
            >
                <div class="flex items-start justify-between gap-4">
                    <div>
                        <h2 class="text-base font-semibold text-ink">{{ title }}</h2>
                        <p v-if="description" class="mt-1 text-xs leading-relaxed text-muted">{{ description }}</p>
                    </div>
                    <button
                        type="button"
                        class="rounded-lg p-1.5 text-muted transition-colors hover:bg-surface-2 hover:text-ink"
                        aria-label="Tutup"
                        @click="emit('close')"
                    >
                        <Icon name="close" :size="18" />
                    </button>
                </div>

                <div class="mt-4">
                    <slot />
                </div>
            </div>
        </div>
    </Teleport>
</template>
