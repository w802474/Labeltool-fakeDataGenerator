/**
 * Utility functions for status mapping and display
 */

export const getStatusText = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'uploaded':
      return 'Uploaded';
    case 'detecting':
      return 'Detecting Text';
    case 'detected':
      return 'OCR Done';
    case 'editing':
      return 'Editing';
    case 'processing':
      return 'Processing';
    case 'completed':
      return 'Processing Complete';
    case 'generated':
      return 'Text Generated';
    case 'error':
    case 'failed':
      return 'Failed';
    default:
      return status;
  }
};

export const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
    case 'generated':
      return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30';
    case 'detected':
      return 'text-purple-600 bg-purple-100 dark:text-purple-400 dark:bg-purple-900/30';
    case 'processing':
      return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
    case 'detecting':
    case 'editing':
      return 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/30';
    case 'uploaded':
      return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
    case 'error':
    case 'failed':
      return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
    default:
      return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
  }
};

export const isStatusCompleted = (status: string): boolean => {
  return ['completed', 'generated'].includes(status.toLowerCase());
};

export const isStatusProcessing = (status: string): boolean => {
  return ['detecting', 'processing'].includes(status.toLowerCase());
};

export const isStatusError = (status: string): boolean => {
  return ['error', 'failed'].includes(status.toLowerCase());
};