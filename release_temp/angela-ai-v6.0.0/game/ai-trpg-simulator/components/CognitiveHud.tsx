import React from 'react';
import { CognitiveState } from '../types';
import { ZapIcon, CpuIcon, ShieldIcon, SparklesIcon } from './icons';

interface CognitiveHudProps {
  cognitiveState: CognitiveState;
}

const MCoreIcon: React.FC<{
    IconComponent: React.FC<{ className?: string }>;
    label: string;
    isActive: boolean;
    color: string;
}> = ({ IconComponent, label, isActive, color }) => (
    <div className={`flex flex-col items-center gap-1 p-1.5 rounded-md transition-all duration-300 ${isActive ? `${color} shadow-lg scale-110` : 'bg-gray-800/50 text-gray-500'}`}>
        <IconComponent className={`w-4 h-4 ${isActive ? 'text-white' : 'fill-current'}`} />
        <span className={`text-[10px] font-bold ${isActive ? 'text-white' : ''}`}>{label}</span>
    </div>
);

const CognitiveHud: React.FC<CognitiveHudProps> = ({ cognitiveState }) => {
    if (!cognitiveState) return null;

    const { vdafScore, activeMCore, chaosFactor } = cognitiveState;
    const vdafPercentage = vdafScore * 100;

    const getBarColor = (score: number) => {
        if (score <= 0.35) return 'bg-green-500';
        if (score <= 0.65) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="p-2 bg-gray-900/60 backdrop-blur-sm border border-gray-700/50 rounded-lg shadow-lg w-full text-white text-sm animate-fade-in">
            <div className="flex items-center gap-3">
                <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                        <span className="font-semibold text-gray-300 text-xs">VDAF</span>
                        <span className="font-mono font-bold text-xs">{vdafScore.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-1.5">
                        <div
                            className={`h-1.5 rounded-full transition-all duration-500 ${getBarColor(vdafScore)}`}
                            style={{ width: `${vdafPercentage}%` }}
                        />
                    </div>
                </div>
                <div className="flex gap-1 relative">
                    {chaosFactor > 0 && activeMCore === 'M6' && (
                         <div className="absolute -top-1 -right-1 z-10 animate-ping">
                             <SparklesIcon className="w-3 h-3 text-purple-400" />
                         </div>
                    )}
                    <MCoreIcon IconComponent={ZapIcon} label="M1" isActive={activeMCore === 'M1'} color="bg-green-600" />
                    <MCoreIcon IconComponent={CpuIcon} label="M3" isActive={activeMCore === 'M3'} color="bg-yellow-600" />
                    <MCoreIcon IconComponent={ShieldIcon} label="M6" isActive={activeMCore === 'M6'} color="bg-red-600" />
                </div>
            </div>
        </div>
    );
};

export default CognitiveHud;
