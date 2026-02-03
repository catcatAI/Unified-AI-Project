import { useState, useEffect, useCallback } from 'react';

function useLocalStorage<T>(
    key: string, 
    initialValue: T,
    merger?: (stored: T, initial: T) => T
): [T, (value: T | ((val: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      const stored = item ? JSON.parse(item) : null;
      
      // If a merger function is provided, always use it to combine
      // stored data with the initial default value. This ensures presets are loaded.
      if (merger) {
          // Provide an empty object-like structure if nothing is stored.
          const storedData = stored || {} as T;
          return merger(storedData, initialValue);
      }
      return stored ?? initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key “${key}”:`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      // Use the functional update form of setState to avoid needing storedValue in dependencies
      setStoredValue(prevValue => {
        const valueToStore = value instanceof Function ? value(prevValue) : value;
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
        return valueToStore;
      });
    } catch (error) {
      console.error(`Error setting localStorage key “${key}”:`, error);
      throw error; // Re-throw to allow callers to handle it.
    }
  }, [key]);
  
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
        if (e.key === key && e.newValue) {
            setStoredValue(JSON.parse(e.newValue));
        }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => {
        window.removeEventListener('storage', handleStorageChange);
    };
  }, [key]);

  return [storedValue, setValue];
}

export default useLocalStorage;