import { useState } from "react";

export interface Toast {
  variant?: "default" | "destructive";
  title?: string;
  description?: string;
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = (toast: Toast) => {
    setToasts(prev => [...prev, toast]);
    // Simple console log for now - in real app would show UI toast
    console.log(`Toast: ${toast.title} - ${toast.description}`);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t !== toast));
    }, 3000);
  };

  return { toast, toasts };
}