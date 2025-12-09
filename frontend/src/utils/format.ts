export const formatNumber = (value?: number, options?: Intl.NumberFormatOptions) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '-'
  return value.toLocaleString(undefined, { maximumFractionDigits: 2, ...options })
}

export const formatPercent = (value?: number, options?: Intl.NumberFormatOptions) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '-'
  return `${value.toLocaleString(undefined, { maximumFractionDigits: 2, ...options })}%`
}

export const formatCurrency = (value?: number, currency = 'EUR', options?: Intl.NumberFormatOptions) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '-'
  return value.toLocaleString(undefined, {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
    ...options,
  })
}

export const formatDate = (value?: string | Date, options?: Intl.DateTimeFormatOptions) => {
  if (!value) return '-'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', ...options })
}

