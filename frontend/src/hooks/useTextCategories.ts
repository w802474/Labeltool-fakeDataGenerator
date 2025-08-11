import { useMemo } from 'react';
import { useAppStore } from '@/stores/useAppStore';

interface CategoryOption {
  value: string;
  label: string;
  color: string;
  description: string;
}

// Text category definitions based on backend classification
const TEXT_CATEGORIES: CategoryOption[] = [
  {
    value: 'japanese_address',
    label: 'Address',
    color: '#FF0000',
    description: 'Japanese address with administrative units'
  },
  {
    value: 'postal_code',
    label: 'Postal Code', 
    color: '#00FF00',
    description: 'Postal code starting with 〒 followed by 7 digits'
  },
  {
    value: 'phone_number',
    label: 'Phone Number',
    color: '#0000FF',
    description: 'Japanese phone number format'
  },
  {
    value: 'pure_number',
    label: 'Pure Number',
    color: '#FFA500',
    description: 'Numbers with comma separators and negative numbers'
  },
  {
    value: 'mixed_id',
    label: 'Mixed ID',
    color: '#800080',
    description: 'Alphanumeric identifiers'
  },
  {
    value: 'other',
    label: 'Other',
    color: '#EF4444',
    description: 'Unclassified text'
  }
];

export const useTextCategories = () => {
  const { updateTextRegionWithUndo } = useAppStore();

  const categoryOptions = useMemo(() => TEXT_CATEGORIES, []);

  const updateRegionCategory = (regionId: string, newCategory: string) => {
    const categoryConfig = TEXT_CATEGORIES.find(cat => cat.value === newCategory);
    if (!categoryConfig) return;

    // Update the region with new category and config
    updateTextRegionWithUndo(regionId, {
      text_category: newCategory,
      category_config: {
        category: newCategory,
        color: categoryConfig.color,
        bgColor: `${categoryConfig.color}26`, // Add transparency
        label: categoryConfig.label,
        description: categoryConfig.description
      },
      is_user_modified: true
    });
  };

  return {
    categoryOptions,
    updateRegionCategory
  };
};