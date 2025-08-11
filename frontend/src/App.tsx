import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Header } from '@/components/Header';
import { HomePage } from '@/pages/HomePage';
import { EditorPage } from '@/pages/EditorPage';
import { useConfirmDialog } from '@/hooks/useConfirmDialog';
import { useToast } from '@/hooks/useToast';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Toast } from '@/components/ui/Toast';

function App() {
  // Initialize confirm dialog and toast for global use
  const { isOpen, options, showConfirm, handleConfirm, handleCancel } = useConfirmDialog();
  const { toasts, removeToast, showSuccess, showError } = useToast();

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
          {/* Header */}
          <Header showConfirm={showConfirm} showToast={showSuccess} showErrorToast={showError} />
          
          {/* Main Content with Routes */}
          <main>
            <Routes>
              <Route path="/" element={<HomePage showConfirm={showConfirm} showToast={showSuccess} showErrorToast={showError} />} />
              <Route path="/editor/:sessionId" element={<EditorPage />} />
            </Routes>
          </main>
          
          {/* Global Confirm Dialog */}
          <ConfirmDialog
            isOpen={isOpen}
            onClose={handleCancel}
            onConfirm={handleConfirm}
            title={options.title}
            message={options.message}
            confirmText={options.confirmText}
            cancelText={options.cancelText}
            type={options.type}
          />
          
          {/* Global Toast Notifications */}
          {toasts.map((toast, index) => (
            <Toast
              key={toast.id}
              message={toast.message}
              type={toast.type}
              duration={toast.duration}
              onClose={() => removeToast(toast.id)}
              index={index}
            />
          ))}
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;