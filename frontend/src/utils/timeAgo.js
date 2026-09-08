const UNITS = [
  ['year', 31536000],
  ['month', 2592000],
  ['week', 604800],
  ['day', 86400],
  ['hour', 3600],
  ['minute', 60],
]

export function timeAgo(isoDateString) {
  const seconds = Math.floor((Date.now() - new Date(isoDateString)) / 1000)
  if (seconds < 60) return 'just now'

  for (const [name, secondsInUnit] of UNITS) {
    const value = Math.floor(seconds / secondsInUnit)
    if (value >= 1) return `${value} ${name}${value > 1 ? 's' : ''} ago`
  }
  return 'just now'
}