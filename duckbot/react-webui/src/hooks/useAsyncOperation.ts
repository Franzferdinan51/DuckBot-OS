import { useState, useCallback, useEffect as React_useEffect } from 'react';

interface AsyncOperationState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseAsyncOperationReturn<T> {
  state: AsyncOperationState<T>;
  execute: (operation: () => Promise<T>) => Promise<T | undefined>;
  reset: () => void;
  setData: (data: T) => void;
  setError: (error: Error) => void;
}

export function useAsyncOperation<T>(): UseAsyncOperationReturn<T> {
  const [state, setState] = useState<AsyncOperationState<T>>({
    data: null,
    loading: false,
    error: null
  });

  const execute = useCallback(async (operation: () => Promise<T>): Promise<T | undefined> => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await operation();
      setState(prev => ({ ...prev, data: result, loading: false, error: null }));
      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error occurred');
      setState(prev => ({ ...prev, loading: false, error: err }));
      throw err;
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null
    });
  }, []);

  const setData = useCallback((data: T) => {
    setState(prev => ({ ...prev, data }));
  }, []);

  const setError = useCallback((error: Error) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  return {
    state,
    execute,
    reset,
    setData,
    setError
  };
}

interface AsyncOptions {
  retries?: number;
  retryDelay?: number;
  onError?: (error: Error) => void;
  onSuccess?: (data: any) => void;
}

export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  dependencies: any[] = [],
  options: AsyncOptions = {}
) {
  const { state, execute, reset } = useAsyncOperation<T>();

  const executeWithRetry = useCallback(async () => {
    const { retries = 2, retryDelay = 1000, onError, onSuccess } = options;

    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= retries + 1; attempt++) {
      try {
        const result = await execute(asyncFunction);
        onSuccess?.(result);
        return result;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        if (attempt <= retries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
        } else {
          onError?.(lastError);
          throw lastError;
        }
      }
    }
  }, [execute, asyncFunction, options]);

  React_useEffect(() => {
    if (dependencies.length > 0) {
      executeWithRetry();
    }
  }, dependencies);

  return { ...state, refetch: executeWithRetry, reset };
}