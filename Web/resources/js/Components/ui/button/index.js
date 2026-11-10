import { cva } from 'class-variance-authority';

export { default as Button } from './Button.vue';

export const buttonVariants = cva(
    'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:pointer-events-none disabled:opacity-50',
    {
        variants: {
            variant: {
                default: 'bg-brand text-brand-ink hover:opacity-90',
                secondary: 'bg-primary-soft text-primary hover:opacity-90',
                outline: 'border border-line bg-surface text-ink hover:bg-surface-2',
                ghost: 'text-muted hover:bg-surface-2 hover:text-ink',
                destructive: 'bg-danger text-white hover:opacity-90',
                link: 'text-primary underline-offset-4 hover:underline',
            },
            size: {
                default: 'h-11 px-3.5 sm:h-9',
                sm: 'h-10 px-3 text-xs sm:h-8',
                lg: 'h-11 px-5',
                icon: 'h-11 w-11 sm:h-8 sm:w-8',
            },
        },
        defaultVariants: {
            variant: 'default',
            size: 'default',
        },
    },
);
