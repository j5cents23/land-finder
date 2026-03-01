export function formatPrice(cents: number): string {
  return `$${(cents / 100).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export function formatPPA(cents: number): string {
  return `${formatPrice(cents)}/ac`
}

export function timeAgo(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const hours = (now - then) / (1000 * 60 * 60)
  if (hours < 1) return "just now"
  if (hours < 24) return `${Math.floor(hours)}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
