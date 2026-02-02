
import React, { useRef, useEffect } from 'react';

const FOCUSABLE_ELEMENTS = [
  'a[href]',
  'button:not([disabled])',
  'textarea:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
];

export const useFocusTrap = <T extends HTMLElement>(initialFocusRef?: React.RefObject<HTMLElement>) => {
  const ref = useRef<T>(null);

  useEffect(() => {
    const trapElement = ref.current;
    if (!trapElement) return;

    const focusableElements = Array.from(
      trapElement.querySelectorAll<HTMLElement>(FOCUSABLE_ELEMENTS.join(', '))
    ).filter((el): el is HTMLElement => el instanceof HTMLElement && el.offsetParent !== null);

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) { // Shift + Tab
        if (document.activeElement === firstElement) {
          lastElement.focus();
          event.preventDefault();
        }
      } else { // Tab
        if (document.activeElement === lastElement) {
          firstElement.focus();
          event.preventDefault();
        }
      }
    };

    trapElement.addEventListener('keydown', handleKeyDown);

    // Focus the initial element if provided, otherwise fall back to the first focusable element.
    if (initialFocusRef?.current) {
        initialFocusRef.current.focus();
    } else {
        firstElement.focus();
    }


    return () => {
      trapElement.removeEventListener('keydown', handleKeyDown);
    };
  }, [initialFocusRef]);

  return ref;
};