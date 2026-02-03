import React, { useState } from 'react';
import { useI18n } from '../context/i18n';

// A simple chevron icon for the toggle button
const ChevronIcon: React.FC<{ open: boolean }> = ({ open }) => (
    <svg className={`w-5 h-5 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
    </svg>
);

interface CollapsiblePanelProps {
  title: string;
  children: React.ReactNode;
  onDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  onClickHeader?: () => boolean; // Return true if an action was taken, false otherwise
  isDropTarget?: boolean;
  defaultOpen?: boolean;
}

const CollapsiblePanel: React.FC<CollapsiblePanelProps> = ({ title, children, onDrop, onClickHeader, isDropTarget = false, defaultOpen = false }) => {
  const { t } = useI18n();
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isDragHovered, setIsDragHovered] = useState(false);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragHovered(true);
  };
  
  const effectiveIsDropTarget = isDropTarget || isDragHovered;

  const handleHeaderClick = () => {
    let actionTaken = false;
    if (onClickHeader) {
        actionTaken = onClickHeader();
    }

    if (actionTaken) {
        // If an action was taken (like moving an item), ensure the panel is open to show the result.
        if (!isOpen) {
            setIsOpen(true);
        }
    } else {
        // If no action was taken, just toggle the panel's state.
        setIsOpen(prev => !prev);
    }
  };

  return (
    <div 
        onDragOver={handleDragOver}
        onDragLeave={() => setIsDragHovered(false)}
        onDrop={(e) => {
            onDrop(e);
            setIsDragHovered(false);
        }}
        className={`bg-gray-900/50 rounded-lg border transition-all duration-200 ${effectiveIsDropTarget ? 'border-indigo-500 ring-2 ring-indigo-500/50' : 'border-gray-700'}`}
    >
      <button
        onClick={handleHeaderClick}
        className="w-full flex justify-between items-center p-2 text-left font-semibold text-gray-200 hover:bg-gray-800/50 rounded-t-lg"
        aria-expanded={isOpen}
        aria-label={isDropTarget ? t('game.inventory.moveToContainer', { containerName: title }) : title}
      >
        <span>{title}</span>
        <ChevronIcon open={isOpen} />
      </button>
      {isOpen && (
        <div className="p-2 border-t border-gray-700 space-y-1">
            {children}
        </div>
      )}
    </div>
  );
};

export default CollapsiblePanel;