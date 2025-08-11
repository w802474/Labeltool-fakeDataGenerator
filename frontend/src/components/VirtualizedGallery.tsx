import React, { useCallback, useMemo } from 'react';
import { FixedSizeGrid as Grid } from 'react-window';
import InfiniteLoader from 'react-window-infinite-loader';
// Define SessionSummary interface to match backend API
interface SessionSummary {
  session_id: string;
  filename: string;
  status: string;
  created_at: string;
  region_count: number;
  image_dimensions: { width: number; height: number };
}
import { SkeletonCard } from '@/components/ui/SkeletonCard';

interface VirtualizedGalleryProps {
  sessions: SessionSummary[];
  loading: boolean;
  hasNextPage: boolean;
  isLoadingMore: boolean;
  onLoadMore: () => Promise<void>;
  onSessionSelect: (sessionId: string) => void;
  onSessionDelete?: (sessionId: string) => void;
  isSelectable?: boolean;
  selectedSessions?: Set<string>;
  onToggleSelect?: (sessionId: string) => void;
  className?: string;
}

// Hook to get responsive column count and item dimensions
const useResponsiveGrid = () => {
  const [gridConfig, setGridConfig] = React.useState({
    columnCount: 6,
    itemWidth: 180,
    itemHeight: 215, // Standard 4:3 ratio
    containerWidth: 1200
  });

  React.useEffect(() => {
    const updateGridConfig = () => {
      const width = window.innerWidth;
      const containerPadding = 64; // Account for container padding
      const gap = 12; // Smaller gap for more compact layout
      
      let columnCount: number;
      let itemWidth: number;
      let containerWidth: number;

      if (width < 640) {
        // Mobile: 2 columns
        columnCount = 2;
        containerWidth = width - containerPadding;
        itemWidth = (containerWidth - gap) / 2;
      } else if (width < 768) {
        // Small tablet: 4 columns
        columnCount = 4;
        containerWidth = Math.min(width - containerPadding, 720);
        itemWidth = (containerWidth - gap * 3) / 4;
      } else if (width < 1024) {
        // Tablet: 6 columns
        columnCount = 6;
        containerWidth = Math.min(width - containerPadding, 960);
        itemWidth = (containerWidth - gap * 5) / 6;
      } else {
        // Desktop: 6 columns
        columnCount = 6;
        containerWidth = Math.min(width - containerPadding, 1200);
        itemWidth = (containerWidth - gap * 5) / 6;
      }

      // Standard card ratio: 4:3 aspect ratio
      const itemHeight = Math.floor(itemWidth * 0.75) + 80; // +80 for text content area

      setGridConfig({
        columnCount,
        itemWidth: Math.floor(itemWidth),
        itemHeight,
        containerWidth
      });
    };

    updateGridConfig();
    window.addEventListener('resize', updateGridConfig);
    
    return () => window.removeEventListener('resize', updateGridConfig);
  }, []);

  return gridConfig;
};

// Individual grid item component
interface GridItemProps {
  columnIndex: number;
  rowIndex: number;
  style: React.CSSProperties;
  data: {
    sessions: SessionSummary[];
    onSessionSelect: (sessionId: string) => void;
    onSessionDelete?: (sessionId: string) => void;
    columnCount: number;
    isLoadingMore: boolean;
    hasNextPage: boolean;
    isSelectable?: boolean;
    selectedSessions?: Set<string>;
    onToggleSelect?: (sessionId: string) => void;
  };
}

const GridItem: React.FC<GridItemProps> = ({ 
  columnIndex, 
  rowIndex, 
  style, 
  data 
}) => {
  const { 
    sessions, 
    onSessionSelect, 
    onSessionDelete,
    columnCount, 
    isLoadingMore, 
    hasNextPage,
    isSelectable,
    selectedSessions,
    onToggleSelect 
  } = data;
  const itemIndex = rowIndex * columnCount + columnIndex;
  const session = sessions[itemIndex];

  // Show skeleton for loading items
  if (!session && (isLoadingMore || hasNextPage)) {
    return (
      <div style={style} className="p-3">
        <SkeletonCard />
      </div>
    );
  }

  // Empty slot
  if (!session) {
    return <div style={style} />;
  }

  return (
    <div style={style} className="p-1.5">
      <SessionCard 
        session={session}
        onSelect={() => onSessionSelect(session.session_id)}
        onDelete={onSessionDelete}
        isSelectable={isSelectable}
        isSelected={selectedSessions?.has(session.session_id) || false}
        onToggleSelect={onToggleSelect}
      />
    </div>
  );
};

// Session card component
interface SessionCardProps {
  session: SessionSummary;
  onSelect: () => void;
  onDelete?: (sessionId: string) => void;
  isSelectable?: boolean;
  isSelected?: boolean;
  onToggleSelect?: (sessionId: string) => void;
}

const SessionCard: React.FC<SessionCardProps> = ({ 
  session, 
  onSelect, 
  onDelete,
  isSelectable = false,
  isSelected = false,
  onToggleSelect 
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusText = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'detected': return 'OCR Done';
      case 'completed': return 'Processing Complete';
      case 'generated': return 'Text Generated';
      case 'processing': return 'Processing';
      case 'failed': return 'Failed';
      default: return status;
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'detected': return 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200';
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200';
      case 'generated': return 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200';
      case 'processing': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  const handleCardClick = (e: React.MouseEvent) => {
    // Prevent card click when clicking on action buttons
    if (isSelectable && onToggleSelect) {
      e.preventDefault();
      onToggleSelect(session.session_id);
    } else {
      onSelect();
    }
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onDelete) {
      onDelete(session.session_id);
    }
  };

  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg border overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer group h-full ${
        isSelected 
          ? 'border-blue-500 ring-2 ring-blue-500 ring-opacity-50' 
          : 'border-gray-200 dark:border-gray-700'
      }`}
      onClick={handleCardClick}
    >
      {/* Image with standard ratio */}
      <div className="relative bg-gray-100 dark:bg-gray-700 overflow-hidden" style={{ aspectRatio: '4/3' }}>
        <img
          src={`/api/v1/sessions/${session.session_id}/image`}
          alt={session.filename}
          className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-200"
          loading="lazy"
        />
        {/* Selection checkbox - top left */}
        {isSelectable && (
          <div className="absolute top-1 left-1 z-10">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelect?.(session.session_id)}
              className="w-4 h-4 text-blue-600 bg-white border-2 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 shadow-sm"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}

        {/* Delete button - top left when not in selection mode */}
        {!isSelectable && onDelete && (
          <button
            onClick={handleDeleteClick}
            className="absolute top-1 left-1 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl z-10"
            title="Delete this item"
            aria-label="Delete this item"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}

        {/* Status Badge - always top right */}
        <div className="absolute top-1 right-1">
          <span className={`px-1 py-0.5 text-xs font-medium rounded ${getStatusColor(session.status)}`}>
            {getStatusText(session.status)}
          </span>
        </div>
        
        {/* Hover overlay - just the animation effect */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-200"></div>
      </div>
      
      {/* Content */}
      <div className="p-2 space-y-1">
        {/* Title */}
        <h3 className="text-xs font-medium text-gray-900 dark:text-gray-100 truncate" title={session.filename}>
          {session.filename}
        </h3>
        
        {/* Date and Regions */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span className="truncate">
            {formatDate(session.created_at)}
          </span>
          <span>
            {session.region_count}r
          </span>
        </div>
        
        {/* Dimensions */}
        <div className="text-xs text-gray-400 dark:text-gray-500 truncate">
          {session.image_dimensions.width} × {session.image_dimensions.height}
        </div>
      </div>
    </div>
  );
};

export const VirtualizedGallery: React.FC<VirtualizedGalleryProps> = ({
  sessions,
  loading,
  hasNextPage,
  isLoadingMore,
  onLoadMore,
  onSessionSelect,
  onSessionDelete,
  isSelectable = false,
  selectedSessions = new Set(),
  onToggleSelect,
  className = ''
}) => {
  const { columnCount, itemWidth, itemHeight, containerWidth } = useResponsiveGrid();
  
  // Calculate total items including potential skeleton items
  const skeletonCount = hasNextPage ? (isLoadingMore ? 6 : 0) : 0;
  const totalItems = sessions.length + skeletonCount;
  const rowCount = Math.ceil(totalItems / columnCount);

  // Check if item is loaded
  const isItemLoaded = useCallback((index: number) => {
    return index < sessions.length;
  }, [sessions.length]);

  // Load more items
  const loadMoreItems = useCallback(async () => {
    if (!isLoadingMore && hasNextPage) {
      await onLoadMore();
    }
  }, [isLoadingMore, hasNextPage, onLoadMore]);

  // Item data for grid
  const itemData = useMemo(() => ({
    sessions,
    onSessionSelect,
    onSessionDelete,
    columnCount,
    isLoadingMore,
    hasNextPage,
    isSelectable,
    selectedSessions,
    onToggleSelect
  }), [sessions, onSessionSelect, onSessionDelete, columnCount, isLoadingMore, hasNextPage, isSelectable, selectedSessions, onToggleSelect]);

  if (loading && sessions.length === 0) {
    return (
      <div className={`grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 max-w-7xl mx-auto ${className}`}>
        {Array.from({ length: 6 }, (_, index) => (
          <SkeletonCard key={`initial-skeleton-${index}`} />
        ))}
      </div>
    );
  }

  return (
    <div className={`max-w-7xl mx-auto ${className}`}>
      <InfiniteLoader
        isItemLoaded={isItemLoaded}
        itemCount={hasNextPage ? totalItems + 1 : totalItems}
        loadMoreItems={loadMoreItems}
        threshold={3}
      >
        {({ onItemsRendered, ref }) => (
          <Grid
            ref={ref}
            columnCount={columnCount}
            columnWidth={itemWidth}
            height={600} // Fixed height for virtual scrolling
            rowCount={rowCount}
            rowHeight={itemHeight}
            width={containerWidth}
            itemData={itemData}
            onItemsRendered={({
              visibleColumnStartIndex,
              visibleColumnStopIndex,
              visibleRowStartIndex,
              visibleRowStopIndex,
            }) => {
              onItemsRendered({
                overscanStartIndex: visibleRowStartIndex * columnCount + visibleColumnStartIndex,
                overscanStopIndex: visibleRowStopIndex * columnCount + visibleColumnStopIndex,
                visibleStartIndex: visibleRowStartIndex * columnCount + visibleColumnStartIndex,
                visibleStopIndex: visibleRowStopIndex * columnCount + visibleColumnStopIndex,
              });
            }}
            className="scrollbar-hide"
          >
            {GridItem}
          </Grid>
        )}
      </InfiniteLoader>
    </div>
  );
};