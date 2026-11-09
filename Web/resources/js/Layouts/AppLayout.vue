<script setup>
import { Link, router, usePage } from '@inertiajs/vue3';
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { Button } from '@/Components/ui/button';
import Icon from '../Components/Icon.vue';
import { useTheme } from '../ui';

const page = usePage();
const { isDark, toggle } = useTheme();

const authUser = computed(() => page.props.authUser ?? null);
const isAdmin = computed(() => authUser.value?.role === 'admin');

const navigation = computed(() => {
    const items = [
        { label: 'Overview', href: '/dashboard', icon: 'overview', match: (url) => url === '/dashboard' || url === '/' },
        { label: 'Transactions', href: '/transactions', icon: 'receipt', match: (url) => url.startsWith('/transactions') },
        { label: 'Stock', href: '/stock', icon: 'stock', match: (url) => url.startsWith('/stock') },
        { label: 'Products', href: '/products', icon: 'product', match: (url) => url.startsWith('/products') },
    ];

    if (isAdmin.value) {
        items.push({ label: 'Akun', href: '/users', icon: 'users', match: (url) => url.startsWith('/users') });
    }

    return items;
});

function logout() {
    router.post('/logout');
}

const currentPath = computed(() => page.url.split('?')[0]);
const flash = computed(() => page.props.flash?.success ?? null);

const toast = ref(flash.value);
let timer = null;

watch(flash, (value) => {
    toast.value = value;
    clearTimeout(timer);
    if (value) {
        timer = setTimeout(() => (toast.value = null), 4500);
    }
});

onBeforeUnmount(() => clearTimeout(timer));
</script>

<template>
    <div class="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
        <aside class="hidden border-r border-line bg-surface lg:flex lg:flex-col lg:sticky lg:top-0 lg:h-screen">
            <div class="px-5 py-5">
                <Link href="/dashboard" class="flex items-center gap-2 text-ink">
                    <span class="h-2.5 w-2.5 rounded-sm bg-primary" aria-hidden="true"></span>
                    <span class="text-base font-semibold tracking-tight">MyVentory</span>
                </Link>
                <p class="mt-1 pl-4.5 text-xs text-muted">Smart inventory</p>
            </div>

            <nav class="mt-2 flex-1 px-3" aria-label="Main">
                <ul class="space-y-1">
                    <li v-for="item in navigation" :key="item.href">
                        <Link
                            :href="item.href"
                            class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors"
                            :class="
                                item.match(currentPath)
                                    ? 'bg-primary-soft font-semibold text-primary'
                                    : 'text-muted hover:bg-surface-2 hover:text-ink'
                            "
                            :aria-current="item.match(currentPath) ? 'page' : undefined"
                        >
                            <Icon :name="item.icon" :size="18" />
                            {{ item.label }}
                        </Link>
                    </li>
                </ul>
            </nav>

            <div class="border-t border-line px-3 py-4">
                <div v-if="authUser" class="mb-2 px-3">
                    <p class="truncate text-sm font-medium text-ink">{{ authUser.name }}</p>
                    <p class="truncate text-xs text-muted">{{ authUser.email }}</p>
                </div>
                <Button variant="ghost" class="w-full justify-start" :aria-pressed="isDark" @click="toggle">
                    <Icon :name="isDark ? 'sun' : 'moon'" :size="18" />
                    {{ isDark ? 'Mode terang' : 'Mode gelap' }}
                </Button>
                <Button variant="ghost" class="mt-1 w-full justify-start" @click="logout">
                    <Icon name="logout" :size="18" />
                    Keluar
                </Button>
                <p class="mt-2 px-3 text-[11px] leading-relaxed text-muted">Data dari kasir dan input manual</p>
            </div>
        </aside>

        <div class="flex min-h-screen min-w-0 flex-col">
            <header class="border-b border-line bg-surface lg:hidden">
                <div class="flex items-center justify-between px-4 py-3">
                    <Link href="/dashboard" class="flex items-center gap-2 text-ink">
                        <span class="h-2.5 w-2.5 rounded-sm bg-primary" aria-hidden="true"></span>
                        <span class="text-base font-semibold">MyVentory</span>
                    </Link>
                    <Button
                        variant="ghost"
                        size="icon"
                        :aria-pressed="isDark"
                        :aria-label="isDark ? 'Aktifkan mode terang' : 'Aktifkan mode gelap'"
                        @click="toggle"
                    >
                        <Icon :name="isDark ? 'sun' : 'moon'" :size="20" />
                    </Button>
                </div>
                <nav class="px-2 pb-2" aria-label="Main">
                    <ul class="grid gap-1" :class="navigation.length > 4 ? 'grid-cols-5' : 'grid-cols-4'">
                        <li v-for="item in navigation" :key="item.href">
                            <Link
                                :href="item.href"
                                class="flex flex-col items-center gap-1 rounded-lg px-1 py-2 text-[11px] leading-tight"
                                :class="
                                    item.match(currentPath)
                                        ? 'bg-primary-soft font-semibold text-primary'
                                        : 'text-muted hover:bg-surface-2 hover:text-ink'
                                "
                                :aria-current="item.match(currentPath) ? 'page' : undefined"
                            >
                                <Icon :name="item.icon" :size="18" />
                                <span class="truncate">{{ item.label }}</span>
                            </Link>
                        </li>
                    </ul>
                </nav>
            </header>

            <main class="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
                <slot />
            </main>

            <footer class="mx-auto w-full max-w-[1400px] px-4 pb-6 text-xs text-muted sm:px-6 lg:px-8">
                MyVentory
            </footer>
        </div>

        <div class="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
            <p
                v-if="toast"
                role="status"
                aria-live="polite"
                class="pointer-events-auto flex items-center gap-2 rounded-lg border border-line bg-surface px-4 py-3 text-sm text-ink shadow-sm"
            >
                <Icon name="check" :size="16" class="text-primary" />
                {{ toast }}
            </p>
        </div>
    </div>
</template>
