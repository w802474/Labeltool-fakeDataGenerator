import React from 'react';
import { VirtualizedGallery } from '@/components/VirtualizedGallery';
// Define SessionSummary interface to match backend API
interface SessionSummary {
  session_id: string;
  filename: string;
  status: string;
  created_at: string;
  region_count: number;
  image_dimensions: { width: number; height: number };
}

interface SessionGalleryProps {
  sessions: SessionSummary[];
  loading: boolean;
  error: string | null;
  hasNextPage: boolean;
  isLoadingMore: boolean;
  onSessionSelect: (sessionId: string) => void;
  onLoadMore: () => Promise<void>;
  onRefresh: () => void;
  onSessionDelete?: (sessionId: string) => void;
  isSelectable?: boolean;
  selectedSessions?: Set<string>;
  onToggleSelect?: (sessionId: string) => void;
  className?: string;
}

export const SessionGallery: React.FC<SessionGalleryProps> = ({
  sessions,
  loading,
  error,
  hasNextPage,
  isLoadingMore,
  onSessionSelect,
  onLoadMore,
  onRefresh,
  onSessionDelete,
  isSelectable = false,
  selectedSessions = new Set(),
  onToggleSelect,
  className = ""
}) => {
  // Initial loading state - let VirtualizedGallery handle its own skeletons

  // Error state
  if (error) {
    return (
      <div className={`flex items-center justify-center min-h-64 ${className}`}>
        <div className="text-center space-y-4">
          <div className="text-red-500 text-2xl">⚠️</div>
          <p className="text-red-600 dark:text-red-400 font-medium">{error}</p>
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (!loading && sessions.length === 0) {
    return (
      <div className={`flex items-center justify-center min-h-64 ${className}`}>
        <div className="text-center space-y-4">
          <div className="text-gray-400 text-4xl">📷</div>
          <p className="text-gray-500 dark:text-gray-400">No processed images yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Images ({sessions.length}{hasNextPage ? '+' : ''})
        </h2>
        
        {/* Loading indicator for load more */}
        {isLoadingMore && (
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <div className="w-4 h-4 border-2 border-blue-200 dark:border-blue-800 border-t-blue-600 dark:border-t-blue-400 rounded-full animate-spin"></div>
            <span>Loading more...</span>
          </div>
        )}
      </div>

      {/* Virtualized Gallery */}
      <VirtualizedGallery
        sessions={sessions}
        loading={loading}
        hasNextPage={hasNextPage}
        isLoadingMore={isLoadingMore}
        onLoadMore={onLoadMore}
        onSessionSelect={onSessionSelect}
        onSessionDelete={onSessionDelete}
        isSelectable={isSelectable}
        selectedSessions={selectedSessions}
        onToggleSelect={onToggleSelect}
        className="animate-scale-in"
      />
    </div>
  );
};