import React, { useState, useRef, useEffect } from 'react';
import { Edit2, Check, X } from 'lucide-react';

interface EditableTextProps {
  text: string;
  onTextChange: (newText: string) => void;
  isModified?: boolean;
  className?: string;
  placeholder?: string;
}

export const EditableText: React.FC<EditableTextProps> = ({
  text,
  onTextChange,
  isModified = false,
  className = '',
  placeholder = 'No text detected'
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(text);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setEditValue(text);
  }, [text]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  const handleSave = () => {
    onTextChange(editValue.trim());
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(text);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const displayText = text || placeholder;
  const isShowingPlaceholder = !text && placeholder;

  if (isEditing) {
    return (
      <div className="flex items-center space-x-1 w-full">
        <input
          ref={inputRef}
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          className="flex-1 px-2 py-1 text-xs border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500"
          placeholder={placeholder}
        />
        <button
          onClick={handleSave}
          className="p-1 text-green-600 hover:text-green-700 hover:bg-green-50 rounded transition-colors"
          title="Save changes"
        >
          <Check className="h-3 w-3" />
        </button>
        <button
          onClick={handleCancel}
          className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded transition-colors"
          title="Cancel editing"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <div 
      className={`group flex items-center justify-between cursor-text hover:bg-gray-50 dark:hover:bg-gray-600 rounded px-1 py-0.5 transition-colors ${className}`}
      onClick={handleStartEdit}
    >
      <span className={`leading-relaxed ${
        isShowingPlaceholder 
          ? 'text-gray-400 dark:text-gray-500 italic' 
          : isModified 
            ? 'text-orange-700 dark:text-orange-300 font-medium' 
            : 'text-gray-700 dark:text-gray-300'
      }`}>
        {displayText}
      </span>
      <Edit2 className="h-3 w-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity ml-1 flex-shrink-0" />
    </div>
  );
};