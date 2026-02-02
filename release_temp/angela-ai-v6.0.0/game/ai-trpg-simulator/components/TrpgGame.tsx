import React from 'react';
import { GamePhase } from '../types'; 
import { SetupScreen } from './SetupScreen'; 
import { GameScreen } from './GameScreen';
import { LoadingSpinner } from './icons';
import { useGameContext } from './context/GameContext';

const AdventureForge: React.FC = () => {
  const { gameState, dispatch } = useGameContext();
  
  const playerCharacter = gameState.characters.find(c => !c.isAI);

  if (gameState.gamePhase === GamePhase.SETUP) {
    return <SetupScreen 
        onStartAdventure={() => dispatch({ type: 'SET_GAME_PHASE', payload: GamePhase.PLAYING })}
    />;
  }

  if (gameState.gamePhase === GamePhase.ERROR) {
    return <div className="flex-1 flex items-center justify-center text-red-400">An unexpected error occurred. Please restart.</div>;
  }
  
  if (!playerCharacter) {
    return <div className="flex-1 flex items-center justify-center"><LoadingSpinner /></div>;
  }

  return <GameScreen playerCharacter={playerCharacter} />;
};

export default AdventureForge;