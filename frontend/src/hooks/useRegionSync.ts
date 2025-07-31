import { useEffect, useRef } from 'react';

/**
 * Custom hook to sync region selection between canvas and list
 */
export const useRegionSync = (selectedRegionId: string | null) => {
  const scrollTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (selectedRegionId) {
      // Clear any existing timeout
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }

      // Add a small delay to ensure the DOM is updated
      scrollTimeout.current = setTimeout(() => {
        const regionElement = document.getElementById(`region-item-${selectedRegionId}`);
        const listContainer = document.getElementById('text-regions-list');
        
        if (regionElement && listContainer) {
          // Calculate if the element is visible
          const containerRect = listContainer.getBoundingClientRect();
          const elementRect = regionElement.getBoundingClientRect();
          
          const isVisible = (
            elementRect.top >= containerRect.top &&
            elementRect.bottom <= containerRect.bottom
          );

          if (!isVisible) {
            // Scroll to the selected region with smooth animation
            regionElement.scrollIntoView({
              behavior: 'smooth',
              block: 'center',
              inline: 'nearest'
            });
          }

          // Add a subtle flash effect to highlight the selection
          regionElement.style.transform = 'scale(1.02)';
          setTimeout(() => {
            if (regionElement) {
              regionElement.style.transform = 'scale(1)';
            }
          }, 200);
        }
      }, 100);
    }

    return () => {
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }
    };
  }, [selectedRegionId]);

  return null;
};