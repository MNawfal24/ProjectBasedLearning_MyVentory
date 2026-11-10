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

/* A bare `YYYY-MM-DD` from the API is a calendar day, not an instant, so it is
   read as a local date instead of UTC midnight. */
const asDate = (value) => {
    if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
        const [year, month, day] = value.split('-').map(Number);

        return new Date(year, month - 1, day);
    }

    return new Date(value);
};

export const formatDate = (value) =>
    new Intl.DateTimeFormat('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }).format(asDate(value));

export const formatShortDate = (value) =>
    new Intl.DateTimeFormat('id-ID', { day: '2-digit', month: 'short' }).format(asDate(value));

export const formatDateTime = (value) =>
    new Intl.DateTimeFormat('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(asDate(value));