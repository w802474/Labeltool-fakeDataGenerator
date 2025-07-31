/**
 * Font utility functions for text preview and scaling
 */
import { TextRegion, Rectangle } from '@/types';

/**
 * Calculate preview font size based on region box scaling
 * This function matches the backend font size estimation logic
 */
export const calculatePreviewFontSize = (region: TextRegion, text?: string): number => {
  // Match backend logic exactly for consistency
  
  // If no original box size recorded, use current size for estimation
  if (!region.original_box_size) {
    // For unmodified regions, estimate from current bounding box (like backend OCR analysis)
    const estimatedSize = Math.max(6, Math.floor(region.bounding_box.height * 0.75));
    return fitFontSizeToBox(estimatedSize, region, text);
  }
  
  // If region size was modified, use the same logic as backend
  if (region.is_size_modified) {
    // Calculate base font size from the ORIGINAL recorded size (match backend exactly)
    const originalHeight = region.original_box_size.height;
    const baseFontSize = Math.max(6, Math.floor(originalHeight * 0.75));
    
    // Calculate scaling factor (match backend exactly)
    const scaleX = region.bounding_box.width / region.original_box_size.width;
    const scaleY = region.bounding_box.height / region.original_box_size.height;
    const avgScale = (scaleX + scaleY) / 2;
    
    // Apply scaling (match backend exactly)
    const scaledSize = Math.max(4, Math.floor(baseFontSize * avgScale));
    
    return fitFontSizeToBox(scaledSize, region, text);
  }
  
  // For unmodified regions with original_box_size, use original size for estimation
  const baseFontSize = Math.max(6, Math.floor(region.original_box_size.height * 0.75));
  return fitFontSizeToBox(baseFontSize, region, text);
};

/**
 * Ensure font size fits within the bounding box
 */
export const fitFontSizeToBox = (initialSize: number, region: TextRegion, text?: string): number => {
  if (!text || text.trim().length === 0) {
    return initialSize;
  }
  
  const bbox = region.bounding_box;
  
  // Conservative approach: ensure text height doesn't exceed 80% of box height
  const maxHeightBasedSize = Math.floor(bbox.height * 0.8);
  
  // If text is very long, also consider width constraints
  const textLength = text.length;
  let widthBasedSize = initialSize;
  
  if (textLength > 0) {
    // More accurate character width estimation based on text type
    let charWidthRatio: number;
    
    if (/[\u4e00-\u9fff]/.test(text)) {
      // Chinese characters are typically square (1:1 ratio)
      charWidthRatio = 1.0;
    } else if (/^[\d\s\.\,\-\+\(\)%$€£¥]+$/.test(text)) {
      // Numbers are typically narrower
      charWidthRatio = 0.5;
    } else {
      // English letters - average width
      charWidthRatio = 0.6;
    }
    
    const estimatedTextWidth = textLength * initialSize * charWidthRatio;
    if (estimatedTextWidth > bbox.width * 0.9) {
      widthBasedSize = Math.floor((bbox.width * 0.9) / (textLength * charWidthRatio));
    }
  }
  
  // Use the smaller of height-based and width-based constraints
  const constrainedSize = Math.min(initialSize, maxHeightBasedSize, widthBasedSize);
  
  // Ensure minimum readable size (match backend minimum)
  return Math.max(4, constrainedSize);
};

/**
 * Select appropriate font family based on text content (matches backend logic)
 */
export const selectFontForText = (text: string): string => {
  if (!text || text.trim().length === 0) {
    return 'Arial';
  }
  
  // Check if text contains Chinese characters
  if (/[\u4e00-\u9fff]/.test(text)) {
    // Chinese text - use a font that supports Chinese
    return 'SimHei, "Microsoft YaHei", "PingFang SC", sans-serif';
  }
  
  // Check if text is primarily numbers
  if (/^[\d\s\.\,\-\+\(\)%$€£¥]+$/.test(text)) {
    // Numbers and common symbols - use a clean, readable font
    return 'Helvetica, Arial, sans-serif';
  }
  
  // Check if text is English letters and basic punctuation
  if (/^[a-zA-Z\s\.\,\!\?\;\:\'\"\-\(\)]+$/.test(text)) {
    // English text - use popular web fonts
    if (text.length > 20) { // Longer text, use readable font
      return '"Times New Roman", serif';
    } else { // Short text, use modern font
      return 'Helvetica, Arial, sans-serif';
    }
  }
  
  // Mixed content or special characters - use Arial as fallback
  return 'Arial, sans-serif';
};

/**
 * Get font family from region properties with fallback
 */
export const getFontFamily = (region: TextRegion, text?: string): string => {
  // If we have text, use intelligent font selection
  if (text && text.trim().length > 0) {
    return selectFontForText(text);
  }
  
  // Otherwise use stored properties or default
  return region.font_properties?.family || 'Arial';
};

/**
 * Get font color from region properties with fallback
 */
export const getFontColor = (region: TextRegion): string => {
  return region.font_properties?.color || 'black';
};

/**
 * Get font weight from region properties with fallback
 */
export const getFontWeight = (region: TextRegion): string => {
  const style = region.font_properties?.style || 'normal';
  return style.includes('bold') ? 'bold' : 'normal';
};

/**
 * Get font style (italic/normal) from region properties
 */
export const getFontStyle = (region: TextRegion): string => {
  const style = region.font_properties?.style || 'normal';
  return style.includes('italic') ? 'italic' : 'normal';
};

/**
 * Check if region box has been modified from original size
 */
export const isRegionSizeModified = (region: TextRegion): boolean => {
  // If explicitly marked as modified, return true
  if (region.is_size_modified === true) {
    return true;
  }
  
  // If no original size recorded, assume not modified (use current size)
  if (!region.original_box_size) {
    return false;
  }
  
  const current = region.bounding_box;
  const original = region.original_box_size;
  
  // Consider modified if dimensions differ by more than 1 pixel (to account for floating point precision)
  const widthDiff = Math.abs(current.width - original.width);
  const heightDiff = Math.abs(current.height - original.height);
  
  return widthDiff > 1 || heightDiff > 1;
};

/**
 * Record original box size for a region (used when region is first created or loaded)
 */
export const recordOriginalBoxSize = (region: TextRegion): TextRegion => {
  if (!region.original_box_size) {
    return {
      ...region,
      original_box_size: { ...region.bounding_box },
      is_size_modified: false
    };
  }
  return region;
};

/**
 * Mark region as size modified (used when user resizes box)
 */
export const markRegionSizeModified = (region: TextRegion): TextRegion => {
  return {
    ...region,
    is_size_modified: true
  };
};