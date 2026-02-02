import React, { useRef } from 'react';
import { Vehicle, RealEstate, DifficultySettings } from '../types';
import { useI18n } from '../context/i18n';
import WorldMap from './WorldMap';
import { TruckIcon, HomeIcon } from './icons';

interface AssetsTabProps {
    location: string;
    onTravel: (locationName: string) => void;
    vehicles: Vehicle[];
    realEstate: RealEstate[];
    difficulty: DifficultySettings;
    mapAssetKey?: string;
    assetCache: Record<string, string>;
    knownLocations: { name: string; description: string; }[];
}

const AssetsTab: React.FC<AssetsTabProps> = ({ location, onTravel, vehicles, realEstate, difficulty, mapAssetKey, assetCache, knownLocations }) => {
    const { t } = useI18n();
    const debounceLock = useRef(false);
    
    const handleTravelClick = (locationName: string) => {
        if (debounceLock.current) return;
        debounceLock.current = true;
        onTravel(locationName);
        setTimeout(() => {
            debounceLock.current = false;
        }, 500);
    };

    const sortedLocations = [...(knownLocations || [])].sort((a, b) => a.name.localeCompare(b.name));
    const sortedVehicles = [...vehicles].sort((a, b) => a.name.localeCompare(b.name));
    const sortedRealEstate = [...realEstate].sort((a, b) => a.name.localeCompare(b.name));
    const mapImageUrl = mapAssetKey ? assetCache[mapAssetKey] : undefined;

    return (
        <div className="space-y-4">
            <div>
                <h3 className="font-semibold text-gray-300 mb-2">{t('game.assets.mapTitle')}</h3>
                <WorldMap mapImageUrl={mapImageUrl} />
            </div>
            
            <div className="border-t border-gray-700 pt-4">
                <h3 className="font-semibold text-gray-300 mb-2">{t('game.assets.knownLocationsTitle')}</h3>
                <div className="space-y-2">
                    {sortedLocations.length > 0 ? sortedLocations.map(loc => {
                        const isActive = loc.name === location;
                        return (
                            <button
                                key={loc.name}
                                disabled={isActive}
                                onClick={() => handleTravelClick(loc.name)}
                                title={loc.description}
                                className={`w-full text-left p-2 rounded-md transition-colors text-sm flex justify-between items-center ${isActive ? 'bg-indigo-800/50 ring-2 ring-indigo-500 cursor-default' : 'bg-gray-900/50 hover:bg-gray-700/80'}`}
                            >
                                <span className={isActive ? 'font-bold text-white' : 'text-gray-300'}>{loc.name}</span>
                                {isActive && <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-600 text-white">Current</span>}
                            </button>
                        );
                    }) : <p className="text-xs text-gray-500 italic">{t('game.empty')}</p>}
                </div>
            </div>

            {difficulty.enableVehicles && sortedVehicles.length > 0 && (
                <div className="border-t border-gray-700 pt-4">
                    <h3 className="font-semibold text-gray-300 mb-2">{t('game.assets.vehiclesTitle')}</h3>
                    <div className="space-y-2">
                        {sortedVehicles.map(v => (
                            <div key={v.id} className="bg-gray-900/50 p-2 rounded-md border border-gray-700 flex gap-3 items-center">
                                <TruckIcon className="w-6 h-6 text-gray-400 flex-shrink-0" />
                                <div>
                                    <p className="font-semibold text-gray-200">{v.name}</p>
                                    <p className="text-xs text-gray-400">{v.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
            
            {difficulty.enableRealEstate && sortedRealEstate.length > 0 && (
                 <div className="border-t border-gray-700 pt-4">
                    <h3 className="font-semibold text-gray-300 mb-2">{t('game.assets.realEstateTitle')}</h3>
                    <div className="space-y-2">
                        {sortedRealEstate.map(r => (
                            <div key={r.name} className="bg-gray-900/50 p-2 rounded-md border border-gray-700 flex gap-3 items-center">
                                <HomeIcon className="w-6 h-6 text-gray-400 flex-shrink-0" />
                                <div>
                                    <p className="font-semibold text-gray-200">{r.name}</p>
                                    <p className="text-xs text-gray-400">{r.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AssetsTab;