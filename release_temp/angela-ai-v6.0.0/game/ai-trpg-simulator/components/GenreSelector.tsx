
import React from 'react';
import { GameGenre } from '../types';
import { useI18n } from '../context/i18n';
import { SwordIcon, BrainIcon } from './icons'; // Re-using existing icons

const PackageIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
    <line x1="1" y1="10" x2="23" y2="10"></line>
  </svg>
);

const CompassIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
    </svg>
);

interface GenreSelectorProps {
    onSelect: (genre: GameGenre) => void;
}

const GenreSelector: React.FC<GenreSelectorProps> = ({ onSelect }) => {
    const { t } = useI18n();
    
    const genres: { id: GameGenre; icon: React.ReactNode }[] = [
        { id: 'adventure', icon: <CompassIcon className="w-10 h-10 mb-2" /> },
        { id: 'action', icon: <SwordIcon className="w-10 h-10 mb-2" /> },
        { id: 'simulation', icon: <PackageIcon className="w-10 h-10 mb-2" /> },
        { id: 'puzzle', icon: <BrainIcon className="w-10 h-10 mb-2" /> },
    ];

    return (
        <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700 shadow-lg">
            <h2 className="text-2xl font-bold text-center mb-6 text-gray-200">{t('frameworkGenerator.genreLabel')}</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {genres.map(genre => (
                    <button
                        key={genre.id}
                        onClick={() => onSelect(genre.id)}
                        className="flex flex-col items-center justify-center p-4 bg-gray-900/50 border border-gray-700 rounded-lg text-gray-300 hover:bg-indigo-900/50 hover:text-white hover:border-indigo-600 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                        {genre.icon}
                        <h3 className="font-semibold">{t(`frameworkGenerator.genres.${genre.id}`)}</h3>
                        <p className="text-xs text-gray-400 text-center mt-1">{t(`frameworkGenerator.genres.${genre.id}Desc`)}</p>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default GenreSelector;
