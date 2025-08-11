import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { clsx } from 'clsx';
import { ChevronDown, Check } from 'lucide-react';

// Global z-index counter for dropdowns
let globalDropdownZIndex = 9999;

interface CategoryOption {
  value: string;
  label: string;
  color: string;
  description: string;
}

interface CategoryDropdownProps {
  value: string;
  options: CategoryOption[];
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
}

export const CategoryDropdown: React.FC<CategoryDropdownProps> = ({
  value,
  options,
  onChange,
  className,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [zIndex, setZIndex] = useState(9999);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const dropdownRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const currentOption = options.find(opt => opt.value === value) || options[0];

  // Check if trigger button is visible in scroll container
  const isElementVisible = (element: Element, container: Element) => {
    const elementRect = element.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    
    // Check if element is within container's visible bounds
    const isVisible = (
      elementRect.top >= containerRect.top &&
      elementRect.bottom <= containerRect.bottom &&
      elementRect.left >= containerRect.left &&
      elementRect.right <= containerRect.right
    );
    
    return isVisible;
  };

  // Update dropdown position when scrolling and check visibility
  useEffect(() => {
    const updatePositionAndCheckVisibility = () => {
      if (isOpen && triggerRef.current) {
        const scrollContainer = triggerRef.current.closest('.overflow-y-auto');
        
        // Check if trigger is still visible in scroll container
        if (scrollContainer && !isElementVisible(triggerRef.current, scrollContainer)) {
          setIsOpen(false);
          return;
        }
        
        // Update position immediately for real-time tracking
        const rect = triggerRef.current.getBoundingClientRect();
        setDropdownPosition({
          top: rect.bottom + window.scrollY + 4,
          left: rect.left + window.scrollX,
          width: rect.width
        });
      }
    };

    if (isOpen) {
      // Listen for scroll events on the scroll container and window
      const scrollContainer = triggerRef.current?.closest('.overflow-y-auto');
      
      window.addEventListener('scroll', updatePositionAndCheckVisibility, { passive: true });
      window.addEventListener('resize', updatePositionAndCheckVisibility);
      
      if (scrollContainer) {
        scrollContainer.addEventListener('scroll', updatePositionAndCheckVisibility, { passive: true });
      }

      return () => {
        window.removeEventListener('scroll', updatePositionAndCheckVisibility);
        window.removeEventListener('resize', updatePositionAndCheckVisibility);
        if (scrollContainer) {
          scrollContainer.removeEventListener('scroll', updatePositionAndCheckVisibility);
        }
      };
    }
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isOpen && triggerRef.current && !triggerRef.current.contains(event.target as Node)) {
        // Check if click is inside the dropdown portal
        const dropdownElement = document.querySelector(`[data-dropdown-id="${zIndex}"]`);
        if (!dropdownElement || !dropdownElement.contains(event.target as Node)) {
          setIsOpen(false);
        }
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, zIndex]);

  const handleOptionSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  const handleToggleOpen = () => {
    if (disabled) return;
    
    if (!isOpen) {
      // When opening, increment global z-index and assign to this dropdown
      globalDropdownZIndex += 1;
      setZIndex(globalDropdownZIndex);
      
      // Calculate dropdown position
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        setDropdownPosition({
          top: rect.bottom + window.scrollY + 4, // 4px gap like mt-1
          left: rect.left + window.scrollX,
          width: rect.width
        });
      }
    }
    setIsOpen(!isOpen);
  };

  return (
    <div className={clsx('relative', className)} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        ref={triggerRef}
        onClick={handleToggleOpen}
        className={clsx(
          'flex items-center justify-between w-full px-2 py-1 text-xs',
          'border border-gray-300 dark:border-gray-600 rounded',
          'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100',
          'transition-colors duration-200',
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer'
        )}
        disabled={disabled}
        type="button"
      >
        <div className="flex items-center space-x-2 min-w-0">
          {/* Color indicator */}
          <div 
            className="w-3 h-3 rounded-sm border border-white/30 flex-shrink-0"
            style={{ backgroundColor: currentOption.color }}
          />
          
          {/* Label */}
          <span className="truncate font-medium">
            {currentOption.label}
          </span>
        </div>
        
        {/* Chevron */}
        <ChevronDown 
          className={clsx(
            'w-3 h-3 transition-transform duration-200 flex-shrink-0',
            isOpen ? 'rotate-180' : ''
          )}
        />
      </button>

      {/* Dropdown Menu - Rendered via Portal */}
      {isOpen && createPortal(
        <div 
          className={clsx(
            'absolute',
            'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600',
            'rounded shadow-xl overflow-y-auto overscroll-contain'
          )}
          data-dropdown-id={zIndex}
          style={{ 
            top: dropdownPosition.top,
            left: dropdownPosition.left,
            width: dropdownPosition.width,
            maxHeight: '120px',
            zIndex: zIndex
          }}
        >
          {options.map((option) => {
            const isSelected = option.value === value;
            
            return (
              <button
                key={option.value}
                onClick={() => handleOptionSelect(option.value)}
                className={clsx(
                  'w-full flex items-center justify-between px-3 py-2 text-xs',
                  'text-left transition-colors duration-200',
                  'hover:bg-gray-100 dark:hover:bg-gray-700',
                  isSelected && 'bg-blue-50 dark:bg-blue-900/30'
                )}
                type="button"
              >
                <div className="flex items-center space-x-2 min-w-0 flex-1">
                  {/* Color indicator */}
                  <div 
                    className="w-3 h-3 rounded-sm border border-white/30 flex-shrink-0"
                    style={{ backgroundColor: option.color }}
                  />
                  
                  {/* Label and description */}
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                      {option.label}
                    </div>
                    <div className="text-gray-500 dark:text-gray-400 truncate text-[10px]">
                      {option.description}
                    </div>
                  </div>
                </div>
                
                {/* Check mark for selected option */}
                {isSelected && (
                  <Check className="w-3 h-3 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                )}
              </button>
            );
          })}
        </div>,
        document.body
      )}
    </div>
  );
};