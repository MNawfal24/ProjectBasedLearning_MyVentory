import { router } from '@inertiajs/vue3';
import { ref } from 'vue';

const STORAGE_KEY = 'myventory-theme';

const isDark = ref(document.documentElement.classList.contains('dark'));

export function useTheme() {
    function toggle() {
        isDark.value = !isDark.value;
        document.documentElement.classList.toggle('dark', isDark.value);
        localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light');
    }

    return { isDark, toggle };
}

/**
 * Inertia visit helper that keeps the current query string for keys not in `changes`.
 */
export function visitWith(params) {
    const query = { ...Object.fromEntries(new URLSearchParams(window.location.search)), ...params };
    Object.keys(query).forEach((key) => {
        if (query[key] === null || query[key] === '' || query[key] === undefined) {
            delete query[key];
        }
    });

    router.get(window.location.pathname, query, { preserveState: true, preserveScroll: true, replace: true });
}
