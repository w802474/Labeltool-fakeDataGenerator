import React, { useMemo } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { clsx } from 'clsx';

interface LegendItem {
  category: string;
  color: string;
  bgColor: string;
  label: string;
  description: string;
  count: number;
}

interface TextClassificationLegendProps {
  className?: string;
}

export const TextClassificationLegend: React.FC<TextClassificationLegendProps> = ({ 
  className 
}) => {
  const { getCurrentDisplayRegions } = useAppStore();
  
  // Get current regions and calculate statistics
  const legendData = useMemo(() => {
    const currentRegions = getCurrentDisplayRegions();
    
    // Count regions by category
    const categoryCounts: Record<string, number> = {};
    const categoryConfigs: Record<string, any> = {};
    
    currentRegions.forEach(region => {
      if (region.category_config && region.text_category) {
        const category = region.text_category;
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
        categoryConfigs[category] = region.category_config;
      }
    });
    
    // Convert to legend items, only showing categories that have regions
    const legendItems: LegendItem[] = Object.entries(categoryCounts).map(([category, count]) => {
      const config = categoryConfigs[category];
      return {
        category,
        color: config.color,
        bgColor: config.bgColor,
        label: config.label,
        description: config.description,
        count
      };
    }).sort((a, b) => b.count - a.count); // Sort by count descending
    
    return legendItems;
  }, [getCurrentDisplayRegions]);
  
  // Don't render if no classified regions
  if (legendData.length === 0) {
    return null;
  }
  
  return (
    <div className={clsx(
      'bg-black/90 text-white px-3 py-2 rounded-lg text-xs z-20 max-w-52',
      className
    )}>
      <div className="text-gray-300 mb-2 text-[10px] font-medium">Text Classification</div>
      <div className="space-y-1.5">
        {legendData.map(item => (
          <div key={item.category} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0 flex-1">
              {/* Enhanced color indicator with border for better visibility */}
              <div 
                className="w-3.5 h-3.5 rounded-sm border-2 border-white/30 flex-shrink-0 shadow-sm"
                style={{ backgroundColor: item.color }}
              />
              
              {/* Label with better spacing */}
              <span className="text-[10px] font-medium truncate" title={item.description}>
                {item.label}
              </span>
            </div>
            
            {/* Count with enhanced styling */}
            <span className="text-[9px] text-gray-300 font-mono bg-gray-700/50 px-1.5 py-0.5 rounded">
              {item.count}
            </span>
          </div>
        ))}
      </div>
      
      {/* Total count */}
      <div className="pt-2 mt-2 border-t border-gray-600 text-[9px] text-gray-400 font-mono">
        Total: {legendData.reduce((sum, item) => sum + item.count, 0)} regions
      </div>
    </div>
  );
};