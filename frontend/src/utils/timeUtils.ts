/**
 * Time formatting utilities
 */

/**
 * Format duration in milliseconds to human readable string
 */
export function formatDuration(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Format time remaining in milliseconds to human readable string
 */
export function formatTimeRemaining(milliseconds: number): string {
  const seconds = Math.ceil(milliseconds / 1000);
  const minutes = Math.ceil(seconds / 60);

  if (minutes > 60) {
    const hours = Math.ceil(minutes / 60);
    return `~${hours}h`;
  } else if (minutes > 1) {
    return `~${minutes}m`;
  } else {
    return `~${seconds}s`;
  }
}

/**
 * Format timestamp to locale string
 */
export function formatTimestamp(timestamp: string | number): string {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

/**
 * Get relative time string (e.g., "2 minutes ago")
 */
export function getRelativeTime(timestamp: string | number): string {
  const now = new Date();
  const past = new Date(timestamp);
  const diffMs = now.getTime() - past.getTime();
  
  const seconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days} day${days > 1 ? 's' : ''} ago`;
  } else if (hours > 0) {
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  } else if (minutes > 0) {
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  } else {
    return 'Just now';
  }
}