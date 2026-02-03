import React, { useState, useEffect } from 'react';
import { Toast } from '../types';

interface ToastProps extends Omit<Toast, 'id'> {
    onDismiss: () => void;
}

const ToastComponent: React.FC<ToastProps> = ({ message, type, onDismiss }) => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(true);
        const timer = setTimeout(() => {
            setIsVisible(false);
        }, 4500);
        const dismissTimer = setTimeout(onDismiss, 5000);

        return () => {
            clearTimeout(timer);
            clearTimeout(dismissTimer);
        };
    }, [onDismiss]);
    
    const colors = {
        success: 'bg-green-500/80 border-green-400',
        info: 'bg-blue-500/80 border-blue-400',
        error: 'bg-red-500/80 border-red-400',
    };

    return (
        <div
            className={`p-3 rounded-lg border text-white shadow-lg backdrop-blur-md transition-all duration-500 ease-in-out transform ${colors[type]} ${
                isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'
            }`}
            role="alert"
        >
            <p className="text-sm font-medium">{message}</p>
        </div>
    );
};

export default ToastComponent;
