import { router } from '@inertiajs/vue3';
import { computed, ref } from 'vue';

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
 * Canvas colours for the charts. ECharts cannot read CSS variables, so the
 * palette is resolved from the stylesheet and recomputed when the theme flips.
 */
export function useChartColors() {
    const { isDark } = useTheme();

    return computed(() => {
        isDark.value;

        const style = getComputedStyle(document.documentElement);
        const read = (name, fallback) => style.getPropertyValue(name).trim() || fallback;

        return {
            ink: read('--color-ink', '#111827'),
            muted: read('--color-muted', '#5b6474'),
            line: read('--color-line', '#e2e8f2'),
            surface: read('--color-surface', '#ffffff'),
            primary: read('--color-primary', '#1e5aef'),
        };
    });
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
