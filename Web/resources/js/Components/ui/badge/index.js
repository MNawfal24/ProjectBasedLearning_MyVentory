import { cva } from 'class-variance-authority';

export { default as Badge } from './Badge.vue';

export const badgeVariants = cva(
    'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors',
    {
        variants: {
            variant: {
                default: 'border-transparent bg-primary-soft text-primary',
                secondary: 'border-transparent bg-surface-2 text-muted',
                destructive: 'border-transparent bg-danger-soft text-danger',
                warning: 'border-transparent bg-accent-soft text-accent',
                outline: 'border-line text-ink',
            },
        },
        defaultVariants: {
            variant: 'default',
        },
    },
);
