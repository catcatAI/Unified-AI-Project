import { useState, useEffect } from 'react';
import { subscribe } from './taskQueueService';

/**
 * A hook that provides a global `isBusy` state.
 * It subscribes to the task queue and returns true if the queue is processing or has pending tasks.
 * This is useful for disabling UI elements across the application during background operations.
 */
export const useGlobalBusyLock = () => {
    const [isBusy, setIsBusy] = useState(false);

    useEffect(() => {
        // subscribe returns an unsubscribe function
        const unsubscribe = subscribe((busy) => {
            setIsBusy(busy);
        });

        return () => {
            unsubscribe();
        };
    }, []);

    return { isBusy };
};
