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

// The avatar carries the owner's own initials; no photo is invented for them.
const initials = computed(() =>
    (authUser.value?.name ?? '')
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0])
        .join('')
        .toUpperCase(),
);

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
    <div class="min-h-screen lg:grid lg:grid-cols-[16rem_1fr]">
        <aside class="hidden border-r border-line bg-surface lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
            <div class="px-5 pt-6 pb-5">
                <Link href="/dashboard" class="flex items-center gap-2.5 text-ink">
                    <img src="/logo.png" alt="" class="h-8 w-8 rounded-md object-contain" />
                    <span class="text-[15px] font-semibold tracking-tight">MyVentory</span>
                </Link>
                <p class="mt-1 pl-[42px] text-2xs text-muted">Back office</p>
            </div>

            <nav class="flex-1 px-3" aria-label="Main">
                <p class="px-3 pb-1.5 text-2xs font-medium text-muted">Menu</p>
                <ul class="space-y-0.5">
                    <li v-for="item in navigation" :key="item.href">
                        <Link
                            :href="item.href"
                            class="flex h-9 items-center gap-2.5 rounded-lg px-3 text-body transition-colors"
                            :class="
                                item.match(currentPath)
                                    ? 'bg-primary-soft font-medium text-primary'
                                    : 'text-muted hover:bg-surface-2 hover:text-ink'
                            "
                            :aria-current="item.match(currentPath) ? 'page' : undefined"
                        >
                            <Icon :name="item.icon" :size="17" />
                            {{ item.label }}
                        </Link>
                    </li>
                </ul>
            </nav>

            <div class="border-t border-line p-3">
                <div v-if="authUser" class="flex items-center gap-2.5 px-2 pb-3">
                    <span
                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary-soft text-2xs font-semibold text-primary"
                        aria-hidden="true"
                    >
                        {{ initials }}
                    </span>
                    <div class="min-w-0">
                        <p class="truncate text-body font-medium text-ink">{{ authUser.name }}</p>
                        <p class="truncate text-2xs text-muted">{{ authUser.email }}</p>
                    </div>
                </div>
                <Button variant="ghost" size="sm" class="w-full justify-start text-body" :aria-pressed="isDark" @click="toggle">
                    <Icon :name="isDark ? 'sun' : 'moon'" :size="16" />
                    {{ isDark ? 'Mode terang' : 'Mode gelap' }}
                </Button>
                <Button variant="ghost" size="sm" class="w-full justify-start text-body" @click="logout">
                    <Icon name="logout" :size="16" />
                    Keluar
                </Button>
            </div>
        </aside>

        <div class="flex min-h-screen min-w-0 flex-col">
            <header class="sticky top-0 z-30 border-b border-line bg-surface lg:hidden">
                <div class="flex items-center justify-between px-4 py-3">
                    <Link href="/dashboard" class="flex min-h-11 items-center gap-2 text-ink">
                        <img src="/logo.png" alt="" class="h-7 w-7 rounded-md object-contain" />
                        <span class="text-[15px] font-semibold tracking-tight">MyVentory</span>
                    </Link>
                    <Button
                        variant="ghost"
                        size="icon"
                        :aria-pressed="isDark"
                        :aria-label="isDark ? 'Aktifkan mode terang' : 'Aktifkan mode gelap'"
                        @click="toggle"
                    >
                        <Icon :name="isDark ? 'sun' : 'moon'" :size="19" />
                    </Button>
                </div>
                <nav class="overflow-x-auto px-2 pb-2" aria-label="Main">
                    <ul class="flex min-w-max gap-0.5">
                        <li v-for="item in navigation" :key="item.href">
                            <Link
                                :href="item.href"
                                class="flex flex-col items-center gap-1 rounded-lg px-3 py-1.5 text-2xs leading-tight whitespace-nowrap"
                                :class="
                                    item.match(currentPath)
                                        ? 'bg-primary-soft font-medium text-primary'
                                        : 'text-muted hover:bg-surface-2 hover:text-ink'
                                "
                                :aria-current="item.match(currentPath) ? 'page' : undefined"
                            >
                                <Icon :name="item.icon" :size="17" />
                                {{ item.label }}
                            </Link>
                        </li>
                    </ul>
                </nav>
            </header>

            <main class="mx-auto w-full max-w-[1440px] flex-1 px-4 py-6 sm:px-6 lg:px-10 lg:py-10">
                <slot />
            </main>

            <footer class="mx-auto w-full max-w-[1440px] px-4 pb-8 text-2xs text-muted sm:px-6 lg:px-10">
                MyVentory &middot; Data dari kasir dan input manual
            </footer>
        </div>

        <div class="pointer-events-none fixed inset-x-0 bottom-5 z-50 flex justify-center px-4">
            <p
                v-if="toast"
                role="status"
                aria-live="polite"
                class="pointer-events-auto flex items-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-body text-ink shadow-raised"
            >
                <Icon name="check" :size="16" class="text-primary" />
                {{ toast }}
            </p>
        </div>
    </div>
</template>
