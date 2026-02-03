import React from 'react';

interface WorldMapProps {
  mapImageUrl?: string;
}

const FallbackMap: React.FC = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-full h-full" viewBox="0 0 100 100">
        <rect width="100" height="100" fill="#374151" />
        <path d="M20 80 Q 40 20, 60 70 T 90 50" stroke="#6b7280" strokeWidth="2" fill="none" />
        <circle cx="30" cy="60" r="3" fill="#9ca3af" />
        <circle cx="70" cy="40" r="4" fill="#9ca3af" />
    </svg>
);


const WorldMap: React.FC<WorldMapProps> = ({ mapImageUrl }) => {
    return (
        <div className="relative w-full aspect-square bg-gray-900/50 border-2 border-gray-700 rounded-md overflow-hidden">
            {mapImageUrl ? (
                <img 
                    src={mapImageUrl} 
                    alt="World Map" 
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ imageRendering: 'pixelated' }}
                />
            ) : (
                <FallbackMap />
            )}
             <div className="absolute inset-0 bg-black/20"></div>
        </div>
    );
};

export default WorldMap;