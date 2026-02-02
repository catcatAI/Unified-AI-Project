import React, { useRef } from 'react';
import { Character } from '../types';
import { SmallLoadingSpinner, RefreshIcon, ImageIcon, SwordIcon, WindIcon, BrainIcon, UserIcon } from './icons';
import { useI18n } from '../context/i18n';
import { useSettings } from '../context/settings';
import { useGameContext } from './context/GameContext';

interface StatusTabProps {
  character: Character;
}

const StatBar: React.FC<{ label: string; value: number; max: number; colorClass: string; ariaLabel: string }> = ({ label, value, max, colorClass, ariaLabel }) => (
  <div className="w-full">
    <div className="flex justify-between items-center mb-0.5">
      <span className="text-xs font-semibold text-gray-400">{label}</span>
      <span className="text-xs font-mono text-gray-300">{value}/{max}</span>
    </div>
    <div
      role="progressbar"
      aria-label={ariaLabel}
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      className="w-full bg-gray-900/80 rounded-full h-2"
    >
      <div className={`${colorClass} h-2 rounded-full transition-all duration-500 ease-out`} style={{ width: `${Math.max(0, (value / max) * 100)}%` }}></div>
    </div>
  </div>
);

const StatusTab: React.FC<StatusTabProps> = ({ character }) => {
  const { t } = useI18n();
  const settings = useSettings();
  const { isBusy, onGeneratePortrait, gameState } = useGameContext();
  const { assetCache } = gameState;
  const debounceLock = useRef(false);

  const handleGenerateClick = () => {
      if (debounceLock.current || isBusy) return;
      debounceLock.current = true;
      onGeneratePortrait(character.name);
      setTimeout(() => {
        debounceLock.current = false;
      }, 500);
  }

  const renderImage = () => {
    const ariaLabel = character.portraitStatus === 'error'
      ? t('game.ariaLabels.regeneratePortrait', { name: character.name })
      : t('game.ariaLabels.generatePortrait', { name: character.name });
      
    const imageUrl = character.portraitAssetKey ? assetCache[character.portraitAssetKey] : undefined;

    if (!settings.enablePortraits) {
        return <div className="w-full h-full flex items-center justify-center"><UserIcon className="w-16 h-16 text-gray-600" /></div>;
    }

    switch (character.portraitStatus) {
        case 'loading':
        case 'queued':
            return <div className="flex items-center justify-center w-full h-full"><SmallLoadingSpinner /></div>;
        case 'error':
            return (
                <button onClick={handleGenerateClick} disabled={isBusy} className="flex items-center justify-center w-full h-full text-red-400 hover:text-red-300 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-red-500" aria-label={ariaLabel}>
                    <RefreshIcon className="w-8 h-8" />
                </button>
            );
        case 'done':
            if (imageUrl) {
                return <img src={imageUrl} alt={t('game.ariaLabels.generatePortrait', { name: character.name })} className="w-full h-full object-cover" />;
            }
        // Fallthrough for done but no URL
        case 'pending':
        default:
             return (
                <button onClick={handleGenerateClick} disabled={isBusy} className="flex items-center justify-center w-full h-full text-indigo-400 hover:text-indigo-300 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500" aria-label={ariaLabel}>
                    <UserIcon className="w-12 h-12" />
                </button>
            );
    }
  };
  
  const { stats } = character;

  return (
    <div className="flex flex-col gap-4 text-white">
      <div className="flex items-center gap-4">
        <div className="w-24 h-24 rounded-md border-2 border-gray-600 bg-gray-900 flex-shrink-0 flex items-center justify-center overflow-hidden" style={{ imageRendering: 'pixelated' }}>
            {renderImage()}
        </div>
        <div className="flex-1 min-w-0">
             <h3 className="text-xl font-bold text-gray-100 truncate">{character.name}</h3>
             <p className="text-sm text-gray-400 capitalize">{character.gender}</p>
        </div>
      </div>
      <p className="text-sm text-gray-300 italic p-2 bg-black/20 rounded-md break-words">{character.description}</p>
      
      <div className="space-y-3">
        <StatBar label="HP" value={stats.hp} max={stats.maxHp} colorClass="bg-red-500" ariaLabel={t('game.ariaLabels.hpBar', { value: stats.hp, max: stats.maxHp })} />
        <StatBar label="MP" value={stats.mp} max={stats.maxMp} colorClass="bg-blue-500" ariaLabel={t('game.ariaLabels.mpBar', { value: stats.mp, max: stats.maxMp })} />
        <StatBar label="SP" value={stats.stamina} max={stats.maxStamina} colorClass="bg-green-500" ariaLabel={t('game.ariaLabels.spBar', { value: stats.stamina, max: stats.maxStamina })}/>
        {(stats.m3LogicStress !== undefined && stats.maxM3LogicStress !== undefined) && <StatBar label="Logic Stress" value={stats.m3LogicStress} max={stats.maxM3LogicStress} colorClass="bg-yellow-500" ariaLabel={`Logic Stress: ${stats.m3LogicStress} of ${stats.maxM3LogicStress}`} />}
        {(stats.m6SecurityShield !== undefined && stats.maxM6SecurityShield !== undefined) && <StatBar label="Security Shield" value={stats.m6SecurityShield} max={stats.maxM6SecurityShield} colorClass="bg-cyan-500" ariaLabel={`Security Shield: ${stats.m6SecurityShield} of ${stats.maxM6SecurityShield}`} />}
      </div>

      <div className="flex justify-around items-center text-center bg-gray-900/50 rounded-md p-2">
            <div className="flex flex-col items-center gap-1" title={t('game.strength')}>
                <SwordIcon className="w-6 h-6 text-red-400"/>
                <span className="text-lg font-bold">{stats.strength}</span>
            </div>
            <div className="flex flex-col items-center gap-1" title={t('game.agility')}>
                <WindIcon className="w-6 h-6 text-green-400"/>
                <span className="text-lg font-bold">{stats.agility}</span>
            </div>
            <div className="flex flex-col items-center gap-1" title={t('game.intelligence')}>
                <BrainIcon className="w-6 h-6 text-blue-400"/>
                <span className="text-lg font-bold">{stats.intelligence}</span>
            </div>
      </div>
    </div>
  );
};

export default StatusTab;