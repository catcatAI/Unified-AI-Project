import React, { useMemo } from 'react';
import { Cinematic, GameState, MValMapObject } from '../types';
import { useI18n } from '../context/i18n';
import { SmallLoadingSpinner, VideoIcon, ImageIcon, UserIcon } from './icons';
import { useGameContext } from './context/GameContext';

interface GameViewProps {
    isFullscreen: boolean;
    isBackground?: boolean;
}

const Atmosphere: React.FC<{ text: string }> = ({ text }) => {
    const lowerText = text.toLowerCase();
    const hasRain = /rain|drizzle|downpour|storm/.test(lowerText);
    const hasFire = /fire|flame|hearth|torch|ember/.test(lowerText);

    return (
        <>
            {hasRain && <div className="absolute inset-0 pointer-events-none bg-repeat" style={{ backgroundImage: `linear-gradient(to bottom, rgba(128, 128, 128, 0.3) 1px, transparent 1px)`, backgroundSize: '2px 20px', animation: 'rain 0.5s linear infinite' }}></div>}
            {hasFire && <div className="absolute inset-0 pointer-events-none bg-orange-400/10" style={{ animation: 'flicker 2s infinite alternate' }}></div>}
            <style>{`
                @keyframes rain { from { background-position: 0 0; } to { background-position: 0 20px; } }
                @keyframes flicker { 0%, 100% { opacity: 1; } 50% { opacity: 0.8; } }
            `}</style>
        </>
    );
};

const TILE_STYLES: Record<string, React.CSSProperties> = {
    air: { background: 'rgba(31, 41, 55, 0.5)' }, // bg-gray-800/50
    ground: { background: 'linear-gradient(135deg, #78350f, #92400e)' }, // amber-800/900
    wall: { 
        backgroundImage: 'linear-gradient(45deg, #4b5563 25%, transparent 25%), linear-gradient(-45deg, #4b5563 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #4b5563 75%), linear-gradient(-45deg, transparent 75%, #4b5563 75%)',
        backgroundSize: '10px 10px',
        backgroundColor: '#6b7280'
    },
    glitch: { background: 'rgb(147 51 234)', animation: 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite' },
    crystal: { background: 'radial-gradient(ellipse at center, #67e8f9, #22d3ee)' }, // cyan-300/400
    abyss: { background: '#000' },
    default: { background: 'rgba(17, 24, 39, 0.5)' }, // bg-gray-900
};

const MapView: React.FC<{ gameState: GameState, isFullscreen: boolean }> = ({ gameState, isFullscreen }) => {
    const { map } = gameState;

    if (!map) return <div className="w-full h-full bg-black flex items-center justify-center"><SmallLoadingSpinner /></div>;

    const { width, height, playerX, playerY, objects, tiles, playerDirection } = map;
    
    const objectMap = new Map<string, MValMapObject>();
    (objects || []).forEach(obj => objectMap.set(`${obj.x},${obj.y}`, obj));

    const rotationClasses = {
        up: '-rotate-90',
        right: 'rotate-0',
        down: 'rotate-90',
        left: 'rotate-180'
    };

    return (
        <div className={`w-full h-full flex items-center justify-center bg-black/50`}>
            <div 
                className="grid"
                style={{ 
                    gridTemplateColumns: `repeat(${width}, minmax(0, 1fr))`,
                    gridTemplateRows: `repeat(${height}, minmax(0, 1fr))`,
                    aspectRatio: `${width} / ${height}`,
                    imageRendering: 'pixelated',
                    maxWidth: '100%',
                    maxHeight: '100%',
                }}
            >
                {tiles.flatMap((row, y) => 
                    row.map((tile, x) => {
                        const isPlayerHere = playerX === x && playerY === y;
                        const object = objectMap.get(`${x},${y}`);
                        const tileStyle = TILE_STYLES[tile] || TILE_STYLES.default;
                        
                        let objectIcon: React.ReactNode = null;
                        if (object) {
                            if (object.icon.startsWith('data:')) {
                                objectIcon = <img src={object.icon} alt={object.name} className="w-full h-full object-contain" />;
                            } else if (object.icon === 'npc') {
                                objectIcon = <UserIcon className="w-full h-full text-pink-400 p-1" />;
                            } else {
                                objectIcon = <div className="text-2xl" title={object.name}>{object.icon}</div>;
                            }
                        }

                        return (
                            <div 
                                key={`${x}-${y}`}
                                className={`aspect-square flex items-center justify-center border border-gray-700/20 relative`}
                                style={tileStyle}
                                title={object ? object.name : `${tile} (${x}, ${y})`}
                            >
                                {isPlayerHere && (
                                    <div className="text-2xl animate-pulse absolute z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                                        <span className={`inline-block transition-transform duration-200 ${rotationClasses[playerDirection]}`}>🧙</span>
                                    </div>
                                )}
                                {objectIcon}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};


const GameView: React.FC<GameViewProps> = ({ isFullscreen, isBackground = false }) => {
    const { gameState } = useGameContext();
    const { gameStyle, locationAssetKey, gameLog, assetCache } = gameState;
    const lastGmMessage = useMemo(() => [...gameLog].reverse().find(m => m.isGM), [gameLog]);
    const locationImageUrl = locationAssetKey ? assetCache[locationAssetKey] : undefined;

    if (gameStyle === 'sandbox') {
        if (isBackground) return null; // Sandbox view is never a background for now
        return (
            <div className="h-full bg-black relative overflow-hidden">
                <MapView gameState={gameState} isFullscreen={isFullscreen} />
            </div>
        );
    }
    
    // Narrative mode (and default) uses location images
    return (
        <div className="w-full h-full bg-gray-900">
            {locationImageUrl ? (
                <img src={locationImageUrl} className="w-full h-full object-cover" alt="" style={{ imageRendering: 'pixelated' }} />
            ) : (
                <div className="w-full h-full bg-gray-800" />
            )}
            {lastGmMessage && <Atmosphere text={lastGmMessage.content} />}
        </div>
    );
};

export default GameView;