import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Github, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAppStore } from '@/stores/useAppStore';
import { apiService } from '@/services/api';

interface HeaderProps {
  showConfirm?: (options: {
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    type?: 'warning' | 'danger' | 'info';
  }) => Promise<boolean>;
  showToast?: (message: string) => void;
  showErrorToast?: (message: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ showConfirm, showToast, showErrorToast }) => {
  const navigate = useNavigate();
  const { settings, setDarkMode, currentSession, updateTextRegions, getCurrentDisplayRegions } = useAppStore();
  const [apiStatus, setApiStatus] = useState<'checking' | 'ready' | 'error'>('checking');

  const toggleDarkMode = () => {
    setDarkMode(!settings.darkMode);
    
    // Apply dark mode to document
    if (!settings.darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleBackToHome = async () => {
    // If there's a current session, save changes and return home
    if (currentSession) {
      try {
        // Save ALL current regions (including deletions, additions, modifications)
        const allCurrentRegions = getCurrentDisplayRegions();
        await updateTextRegions(allCurrentRegions, 'auto', false);
        
        // Navigate to home page
        navigate('/');
        
      } catch (error) {
        showErrorToast?.('Failed to save changes. Please try again.');
        return; // Don't navigate home if save failed
      }
    } else {
      // No current session, just go to home
      navigate('/');
    }
  };

  // Check API status on component mount
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        await apiService.checkHealth();
        setApiStatus('ready');
      } catch (error) {
        setApiStatus('error');
      }
    };

    checkApiStatus();
    // Recheck every 30 seconds
    const interval = setInterval(checkApiStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Initialize dark mode and update when settings change
  useEffect(() => {
    if (settings.darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [settings.darkMode]);

  return (
    <header className="border-b bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div 
            className="flex items-center space-x-3 cursor-pointer transition-transform hover:scale-105"
            onClick={handleBackToHome}
            title="Return to Home"
          >
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">LabelTool</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Intelligent Text Detection & Removal
              </p>
            </div>
          </div>

          {/* Navigation and Actions */}
          <div className="flex items-center space-x-4">
            {/* Dark Mode Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleDarkMode}
              title={settings.darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              className="text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100"
            >
              {settings.darkMode ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>

            {/* GitHub Link */}
            <Button
              variant="ghost"
              size="icon"
              asChild
              className="text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100"
            >
              <a
                href="https://github.com/w802474/Labeltool-fakeDataGenerator/tree/main"
                target="_blank"
                rel="noopener noreferrer"
                title="View on GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
            </Button>

            {/* API Status Indicator */}
            <div className={`hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full border ${
              apiStatus === 'ready' 
                ? 'bg-green-50 dark:bg-green-900 border-green-200 dark:border-green-700'
                : apiStatus === 'error'
                ? 'bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700'
                : 'bg-yellow-50 dark:bg-yellow-900 border-yellow-200 dark:border-yellow-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === 'ready'
                  ? 'bg-green-500 animate-pulse'
                  : apiStatus === 'error'
                  ? 'bg-red-500'
                  : 'bg-yellow-500 animate-pulse'
              }`}></div>
              <span className={`text-xs font-medium ${
                apiStatus === 'ready'
                  ? 'text-green-700 dark:text-green-400'
                  : apiStatus === 'error'
                  ? 'text-red-700 dark:text-red-400'
                  : 'text-yellow-700 dark:text-yellow-400'
              }`}>
                {apiStatus === 'ready' ? 'API Ready' : apiStatus === 'error' ? 'API Error' : 'Checking API...'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};