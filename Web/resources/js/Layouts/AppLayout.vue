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
        { label: 'Prediksi', href: '/predictions', icon: 'overview', match: (url) => url.startsWith('/predictions') },
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

// Search jumps to the product ledger, which already filters by name.
const query = ref('');
const currentSearch = computed(() => new URLSearchParams(page.url.split('?')[1] ?? '').get('search') ?? '');

watch(
    () => page.url,
    () => {
        query.value = currentSearch.value;
    },
    { immediate: true },
);

function search() {
    const value = query.value.trim();

    router.get('/products', value ? { search: value } : {}, { preserveScroll: true });
}

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
        <aside class="hidden bg-brand text-brand-ink lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
            <div class="px-5 pt-6 pb-5">
                <Link href="/dashboard" class="flex items-center gap-2.5 text-brand-ink">
                    <img src="/logo.png" alt="" class="h-8 w-8 rounded-md bg-white object-contain p-1" />
                    <span class="text-[15px] font-semibold tracking-tight">MyVentory</span>
                </Link>
                <p class="mt-1 pl-[42px] text-2xs text-white/90">Back office</p>
            </div>

            <nav class="flex-1 px-3" aria-label="Main">
                <p class="px-3 pb-1.5 text-2xs font-medium text-white/90">Menu</p>
                <ul class="space-y-1">
                    <li v-for="item in navigation" :key="item.href">
                        <Link
                            :href="item.href"
                            class="flex h-10 items-center gap-2.5 rounded-lg px-3 text-body transition-colors"
                            :class="
                                item.match(currentPath)
                                    ? 'bg-white font-medium text-brand'
                                    : 'text-brand-ink hover:bg-white/10'
                            "
                            :aria-current="item.match(currentPath) ? 'page' : undefined"
                        >
                            <Icon :name="item.icon" :size="17" />
                            {{ item.label }}
                        </Link>
                    </li>
                </ul>
            </nav>

            <div class="border-t border-white/20 p-3">
                <div v-if="authUser" class="flex items-center gap-2.5 rounded-lg bg-white/10 px-3 py-2.5">
                    <span
                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-2xs font-semibold text-brand"
                        aria-hidden="true"
                    >
                        {{ initials }}
                    </span>
                    <div class="min-w-0">
                        <p class="truncate text-body font-medium text-brand-ink">{{ authUser.name }}</p>
                        <p class="truncate text-2xs text-white/90">{{ authUser.email }}</p>
                    </div>
                </div>
                <button
                    type="button"
                    class="mt-2 flex h-10 w-full items-center gap-2.5 rounded-lg px-3 text-body text-brand-ink transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                    :aria-pressed="isDark"
                    @click="toggle"
                >
                    <Icon :name="isDark ? 'sun' : 'moon'" :size="17" />
                    {{ isDark ? 'Mode terang' : 'Mode gelap' }}
                </button>
                <button
                    type="button"
                    class="flex h-10 w-full items-center gap-2.5 rounded-lg px-3 text-body text-brand-ink transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                    @click="logout"
                >
                    <Icon name="logout" :size="17" />
                    Keluar
                </button>
            </div>
        </aside>

        <div class="flex min-h-screen min-w-0 flex-col">
            <header class="sticky top-0 z-30 hidden border-b border-line bg-surface lg:block">
                <div class="mx-auto flex h-16 w-full max-w-[1440px] items-center gap-6 px-10">
                    <form class="relative w-full max-w-sm" role="search" @submit.prevent="search">
                        <label for="global-search" class="sr-only">Cari produk</label>
                        <span class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted">
                            <Icon name="search" :size="17" />
                        </span>
                        <input
                            id="global-search"
                            v-model="query"
                            type="search"
                            class="field pl-9"
                            placeholder="Cari produk"
                        />
                    </form>

                    <div class="ml-auto flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="icon"
                            :aria-pressed="isDark"
                            :aria-label="isDark ? 'Aktifkan mode terang' : 'Aktifkan mode gelap'"
                            @click="toggle"
                        >
                            <Icon :name="isDark ? 'sun' : 'moon'" :size="19" />
                        </Button>
                        <div v-if="authUser" class="flex items-center gap-2.5 pl-2">
                            <span
                                class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-soft text-2xs font-semibold text-primary"
                                aria-hidden="true"
                            >
                                {{ initials }}
                            </span>
                            <div class="hidden xl:block">
                                <p class="text-body font-medium text-ink">{{ authUser.name }}</p>
                                <p class="text-2xs text-muted">{{ authUser.email }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <header class="sticky top-0 z-30 border-b border-line bg-brand text-brand-ink lg:hidden">
                <div class="flex items-center justify-between px-4 py-3">
                    <Link href="/dashboard" class="flex min-h-11 items-center gap-2 text-brand-ink">
                        <img src="/logo.png" alt="" class="h-7 w-7 rounded-md bg-white object-contain p-0.5" />
                        <span class="text-[15px] font-semibold tracking-tight">MyVentory</span>
                    </Link>
                    <div class="flex items-center gap-1">
                        <button
                            type="button"
                            class="flex h-11 w-11 items-center justify-center rounded-lg text-brand-ink transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                            :aria-pressed="isDark"
                            :aria-label="isDark ? 'Aktifkan mode terang' : 'Aktifkan mode gelap'"
                            @click="toggle"
                        >
                            <Icon :name="isDark ? 'sun' : 'moon'" :size="19" />
                        </button>
                        <button
                            type="button"
                            class="flex h-11 w-11 items-center justify-center rounded-lg text-brand-ink transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                            aria-label="Keluar"
                            @click="logout"
                        >
                            <Icon name="logout" :size="19" />
                        </button>
                    </div>
                </div>
                <nav class="overflow-x-auto px-2 pb-2" aria-label="Main">
                    <ul class="flex min-w-max gap-1">
                        <li v-for="item in navigation" :key="item.href">
                            <Link
                                :href="item.href"
                                class="flex flex-col items-center gap-1 rounded-lg px-3 py-1.5 text-2xs leading-tight whitespace-nowrap"
                                :class="
                                    item.match(currentPath)
                                        ? 'bg-white font-medium text-brand'
                                        : 'text-brand-ink hover:bg-white/10'
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

            <main class="mx-auto w-full max-w-[1440px] flex-1 px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
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
