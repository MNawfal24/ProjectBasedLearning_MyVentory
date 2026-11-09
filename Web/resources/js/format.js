const rupiah = new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
});

const compact = new Intl.NumberFormat('id-ID', {
    notation: 'compact',
    maximumFractionDigits: 1,
});

const decimal = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 2 });

export const formatCurrency = (value) => rupiah.format(Number(value) || 0);

export const formatCompact = (value) => compact.format(Number(value) || 0);

export const formatNumber = (value) => decimal.format(Number(value) || 0);

export const formatDate = (value) =>
    new Intl.DateTimeFormat('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));

export const formatShortDate = (value) =>
    new Intl.DateTimeFormat('id-ID', { day: '2-digit', month: 'short' }).format(new Date(value));

export const formatDateTime = (value) =>
    new Intl.DateTimeFormat('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(new Date(value));
