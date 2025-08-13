import { useEffect, useCallback } from 'react';
import { useAppStore } from '@/stores/useAppStore';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  action: () => void | Promise<void>;
  description: string;
}

export const useKeyboardShortcuts = () => {
  const {
    currentSession,
    processTextRemovalAsync,
    downloadResult,
    deleteSession,
    setSelectedRegion,
    canvasState,
    removeTextRegion,
    setActiveTool,
    undoLastCommand,
    canUndo,
  } = useAppStore();

  const shortcuts: KeyboardShortcut[] = [
    {
      key: 'v',
      action: () => {
        setActiveTool('select');
      },
      description: 'Select tool',
    },
    {
      key: 'z',
      ctrlKey: true,
      action: async () => {
        if (canUndo()) {
          await undoLastCommand();
        }
      },
      description: 'Undo last operation (Ctrl+Z)',
    },
    {
      key: 'z',
      metaKey: true, // Command key on macOS
      action: async () => {
        if (canUndo()) {
          await undoLastCommand();
        }
      },
      description: 'Undo last operation (Cmd+Z)',
    },
    {
      key: 'p',
      ctrlKey: true,
      action: async () => {
        if (currentSession && (currentSession.status === 'detected' || currentSession.status === 'editing')) {
          try {
            await processTextRemovalAsync();
          } catch (error) {
            console.error('Failed to start async processing via keyboard shortcut:', error);
          }
        }
      },
      description: 'Process text removal',
    },
    {
      key: 'd',
      ctrlKey: true,
      action: () => {
        if (currentSession && currentSession.status === 'removed') {
          downloadResult();
        }
      },
      description: 'Download result',
    },
    {
      key: 'Escape',
      action: () => {
        setSelectedRegion(null);
      },
      description: 'Deselect region',
    },
    {
      key: 'Delete',
      action: () => {
        if (canvasState.selectedRegionId) {
          removeTextRegion(canvasState.selectedRegionId);
          setSelectedRegion(null);
        }
      },
      description: 'Delete selected region',
    },
    {
      key: 'Backspace',
      action: () => {
        if (canvasState.selectedRegionId) {
          removeTextRegion(canvasState.selectedRegionId);
          setSelectedRegion(null);
        }
      },
      description: 'Delete selected region',
    },
  ];

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't trigger shortcuts if user is typing in an input
    const target = event.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.contentEditable === 'true') {
      return;
    }

    const matchingShortcut = shortcuts.find(shortcut => {
      return (
        shortcut.key.toLowerCase() === event.key.toLowerCase() &&
        !!shortcut.ctrlKey === event.ctrlKey &&
        !!shortcut.metaKey === event.metaKey &&
        !!shortcut.shiftKey === event.shiftKey &&
        !!shortcut.altKey === event.altKey
      );
    });

    if (matchingShortcut) {
      event.preventDefault();
      event.stopPropagation();
      matchingShortcut.action();
    }
  }, [shortcuts]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    shortcuts: shortcuts.map(({ action, ...shortcut }) => shortcut),
  };
};