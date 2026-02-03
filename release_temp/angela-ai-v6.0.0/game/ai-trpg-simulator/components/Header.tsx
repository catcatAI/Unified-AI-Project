import React from 'react';
import { useI18n } from '../context/i18n';
import { GameMasterIcon, SparklesIcon, CubeIcon, SettingsIcon, BookIcon } from './icons';

export type Tool = 'adventureForge' | 'creativeHub' | 'model' | 'codex';

interface HeaderProps {
  activeTool: Tool;
  setActiveTool: (tool: Tool) => void;
  onOpenSettings: () => void;
}

interface NavButtonProps {
    label: string;
    icon: React.ReactNode;
    isActive: boolean;
    onClick: () => void;
}

const NavButton: React.FC<NavButtonProps> = ({ label, icon, isActive, onClick }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400 ${
            isActive ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700/50'
        }`}
    >
        {icon}
        <span className="hidden sm:inline">{label}</span>
    </button>
);


const Header: React.FC<HeaderProps> = ({ activeTool, setActiveTool, onOpenSettings }) => {
  const { t } = useI18n();

  return (
    <header className="flex-shrink-0 bg-gray-800/50 border-b border-gray-700 p-3 shadow-lg backdrop-blur-sm z-20">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-100 hidden md:block">{t('suite.title')}</h1>
        <div className="flex items-center gap-2 flex-grow justify-end">
            <nav className="flex items-center gap-1 sm:gap-2 p-1 bg-gray-900/50 rounded-lg w-full sm:w-auto justify-around">
                <NavButton
                    label={t('suite.navAdventureForge')}
                    icon={<GameMasterIcon className="w-5 h-5" />}
                    isActive={activeTool === 'adventureForge'}
                    onClick={() => setActiveTool('adventureForge')}
                />
                 <NavButton
                    label={t('suite.navCreativeHub')}
                    icon={<SparklesIcon className="w-5 h-5" />}
                    isActive={activeTool === 'creativeHub'}
                    onClick={() => setActiveTool('creativeHub')}
                />
                 <NavButton
                    label={t('suite.navModel')}
                    icon={<CubeIcon className="w-5 h-5" />}
                    isActive={activeTool === 'model'}
                    onClick={() => setActiveTool('model')}
                />
                 <NavButton
                    label={t('suite.navCodex')}
                    icon={<BookIcon className="w-5 h-5" />}
                    isActive={activeTool === 'codex'}
                    onClick={() => setActiveTool('codex')}
                />
            </nav>
            <button
                onClick={onOpenSettings}
                aria-label={t('suite.settings.title')}
                className="p-2 rounded-md text-gray-300 hover:bg-gray-700/50 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
                <SettingsIcon className="w-5 h-5" />
            </button>
        </div>
      </div>
    </header>
  );
};

export default Header;