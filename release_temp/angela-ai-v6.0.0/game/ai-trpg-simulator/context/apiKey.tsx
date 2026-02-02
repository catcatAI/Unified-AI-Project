import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { LoadingSpinner } from '../components/icons';

// This is a simplified stub. In a real environment, this might be provided by the platform.
declare global {
    interface AIStudio {
        hasSelectedApiKey: () => Promise<boolean>;
        openSelectKey: () => Promise<void>;
    }

    interface Window {
        aistudio?: AIStudio;
    }
}


interface ApiKeyContextType {
  isKeySelected: boolean;
  selectKey: () => Promise<void>;
  resetKeySelection: () => void;
}

const ApiKeyContext = createContext<ApiKeyContextType | undefined>(undefined);

export const ApiKeyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isKeySelected, setIsKeySelected] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  const checkKey = useCallback(async () => {
    setIsChecking(true);
    if (window.aistudio?.hasSelectedApiKey) {
      try {
        const hasKey = await window.aistudio.hasSelectedApiKey();
        setIsKeySelected(hasKey);
      } catch (e) {
        console.error("Error checking for API key:", e);
        setIsKeySelected(false);
      }
    } else {
        // If the aistudio object doesn't exist, assume we are in a dev environment
        // where the key is provided via other means (e.g. env vars)
        setIsKeySelected(true);
    }
    setIsChecking(false);
  }, []);

  useEffect(() => {
    checkKey();
  }, [checkKey]);

  const selectKey = useCallback(async () => {
    if (window.aistudio?.openSelectKey) {
      await window.aistudio.openSelectKey();
      // Assume success and update state immediately to improve UI responsiveness
      setIsKeySelected(true);
      // Re-check in the background to confirm
      checkKey();
    } else {
        // In a dev environment, this button might not do anything.
        // We can simulate the check to ensure the state is correct.
        checkKey();
    }
  }, [checkKey]);

  const resetKeySelection = useCallback(() => {
    // This is primarily for handling errors where the selected key is no longer valid.
    setIsKeySelected(false);
  }, []);
  
  const value = useMemo(() => ({ isKeySelected, selectKey, resetKeySelection }), [isKeySelected, selectKey, resetKeySelection]);

  // Provider now simply provides the context value without blocking children.
  return (
    <ApiKeyContext.Provider value={value}>
      {children}
    </ApiKeyContext.Provider>
  );
};

export const useApiKey = (): ApiKeyContextType => {
  const context = useContext(ApiKeyContext);
  if (context === undefined) {
    throw new Error('useApiKey must be used within an ApiKeyProvider');
  }
  return context;
};