import React from 'react';
import { useI18n } from '../context/i18n';
import WorldMap from './WorldMap';

interface WorldTabProps {
  location: string;
  onTravel: (locationName: string) => void;
  mapImageUrl?: string;
  knownLocations: { name: string; description: string; }[];
}

const WorldTab: React.FC<WorldTabProps> = ({ location, onTravel, mapImageUrl, knownLocations }) => {
    const { t } = useI18n();

    return (
        <div className="flex flex-col h-full gap-2">
             <p className="text-sm text-gray-400 flex-shrink-0">Current Location: <span className="font-bold text-white">{location}</span></p>
             <div className="flex-1 min-h-0 flex items-center justify-center">
                <div className="w-full max-w-full aspect-square">
                    <WorldMap location={location} onTravel={onTravel} mapImageUrl={mapImageUrl} knownLocations={knownLocations} />
                </div>
             </div>
        </div>
    );
};

export default WorldTab;