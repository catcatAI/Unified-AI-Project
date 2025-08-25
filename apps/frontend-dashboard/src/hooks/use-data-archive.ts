// Custom hook for data archive functionality
import { useState, useEffect, useCallback } from 'react';
import { dataArchiveService, ArchiveEntry } from '@/lib/data-archive';

// Hook for managing data archive
export function useDataArchive() {
  const [entries, setEntries] = useState<ArchiveEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all archive entries
  const fetchEntries = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dataArchiveService.getAllEntries();
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch archive entries');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch entries by type
  const fetchEntriesByType = useCallback(async (type: ArchiveEntry['type']) => {
    try {
      setLoading(true);
      setError(null);
      const data = await dataArchiveService.getEntriesByType(type);
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to fetch ${type} entries`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Save a new entry
  const saveEntry = useCallback(async (entry: Omit<ArchiveEntry, 'id' | 'createdAt'>) => {
    try {
      const savedEntry = await dataArchiveService.saveEntry(entry);
      // Refresh the entries list
      await fetchEntries();
      return savedEntry;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save entry');
      throw err;
    }
  }, [fetchEntries]);

  // Delete an entry
  const deleteEntry = useCallback(async (id: string) => {
    try {
      await dataArchiveService.deleteEntry(id);
      // Refresh the entries list
      await fetchEntries();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete entry');
      throw err;
    }
  }, [fetchEntries]);

  // Clear all entries
  const clearAll = useCallback(async () => {
    try {
      await dataArchiveService.clearAll();
      // Refresh the entries list
      await fetchEntries();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear entries');
      throw err;
    }
  }, [fetchEntries]);

  // Initialize by fetching entries
  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  return {
    entries,
    loading,
    error,
    fetchEntries,
    fetchEntriesByType,
    saveEntry,
    deleteEntry,
    clearAll,
  };
}

// Hook for specific type of archive entries
export function useArchiveByType(type: ArchiveEntry['type']) {
  const [entries, setEntries] = useState<ArchiveEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEntries = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dataArchiveService.getEntriesByType(type);
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to fetch ${type} entries`);
    } finally {
      setLoading(false);
    }
  }, [type]);

  // Initialize by fetching entries
  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  return {
    entries,
    loading,
    error,
    refresh: fetchEntries,
  };
}