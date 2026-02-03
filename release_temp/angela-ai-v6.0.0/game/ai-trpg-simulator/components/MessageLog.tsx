import React, { useRef, useEffect, useCallback } from 'react';
import { Message, DiceRoll, Cinematic, Task, Character, Sfx } from '../types';
import { SpeakerIcon, SoundWaveIcon, SmallLoadingSpinner, PlayIcon, VideoIcon, ImageIcon, WitchHatIcon } from './icons';
import { useI18n } from '../context/i18n';
import DynamicSfxPlayer from './DynamicSfxPlayer';
import DiceRollDisplay from './DiceRollDisplay';
import { useGameContext } from './context/GameContext';

interface MessageItemProps {
    msg: Message;
    getAuthorStyle: (author: string, isGM: boolean) => string;
    isPending: boolean;
    isTtsEnabled: boolean;
    playingMessageKey: string | null;
    onPlayTtsRequest: (messageId: string) => void;
    getTtsAriaLabel: (author: string, messageId: string) => string;
    isAnyTtsLoading: boolean;
    playerCharacterName: string;
    cinematic?: Cinematic;
    assetCache: Record<string, string>;
    onGenerateVideoClick: (messageId: string, prompt: string) => void;
    isBusy: boolean;
}

const MemoizedMessageItem: React.FC<MessageItemProps> = React.memo(({
    msg, getAuthorStyle, isPending, isTtsEnabled, playingMessageKey, onPlayTtsRequest, getTtsAriaLabel, isAnyTtsLoading, playerCharacterName, assetCache, onGenerateVideoClick, isBusy
}) => {
    const { t } = useI18n();

    const bgmRegex = /\[BGM_MOOD:([a-zA-Z]+)\]/g;
    const sfxTagRegex = /\[SFX:([^\]]+)\]/g;
    const cinematicTagRegex = /\[CINEMATIC:([^\]]+)\]/g;

    const contentWithoutTags = (msg.content ?? '')
        .replace(bgmRegex, '')
        .replace(sfxTagRegex, '')
        .replace(cinematicTagRegex, '')
        .trim();
    
    const bgmMatches = [...(msg.content ?? '').matchAll(bgmRegex)];

    // Check if there's any visible content to render
    const hasVisibleContent = contentWithoutTags || msg.dialogue || msg.diceRoll || msg.cinematic || msg.sfx || bgmMatches.length > 0 || msg.interpretedPlayerAction;
    if (!hasVisibleContent && !isPending) return null;

    const shouldShowTtsButton = isTtsEnabled && msg.author !== playerCharacterName && (msg.dialogue || (msg.isGM && contentWithoutTags));

    return (
        <div key={msg.id}>
            {bgmMatches.map((match, index) => <BgmMoodDisplay key={index} mood={match[1]} />)}
            {msg.cinematic && <CinematicDisplay cinematic={msg.cinematic} messageId={msg.id} assetCache={assetCache} onGenerateVideoClick={onGenerateVideoClick} isBusy={isBusy} />}
            {msg.diceRoll && !/hit|miss/i.test(msg.content) && <DiceRollDisplay roll={msg.diceRoll} />}
            {(contentWithoutTags || msg.dialogue || msg.sfx || isPending || msg.interpretedPlayerAction) && (
                <div className="mt-2">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <p className={`font-bold ${getAuthorStyle(msg.author, msg.isGM)}`}>{msg.author}</p>
                            {isPending && <SmallLoadingSpinner />}
                        </div>
                        {shouldShowTtsButton && (
                            <button onClick={() => onPlayTtsRequest(msg.id)} disabled={isAnyTtsLoading && playingMessageKey !== msg.id} className="p-1 rounded-full text-gray-400 hover:bg-gray-700 disabled:text-gray-600" aria-label={getTtsAriaLabel(msg.author, msg.id)}>
                                {playingMessageKey === msg.id + '-loading' ? <SmallLoadingSpinner /> : playingMessageKey === msg.id ? <SoundWaveIcon className="w-4 h-4 text-indigo-400" /> : <SpeakerIcon className="w-4 h-4" />}
                            </button>
                        )}
                    </div>
                    {/* Render action (content) as italic if dialogue exists, and render dialogue separately. */}
                    {contentWithoutTags && <p className={`whitespace-pre-wrap ${msg.dialogue ? 'text-gray-400 italic' : 'text-gray-300'}`}>{contentWithoutTags}</p>}
                    
                    {/* Character Agency Interpretation */}
                    {msg.interpretedPlayerAction && (
                        <div className="mt-1 pl-3 py-1 border-l-2 border-purple-400/50 flex items-start gap-2">
                            <WitchHatIcon className="w-4 h-4 text-purple-400/80 flex-shrink-0 mt-0.5" />
                            <p className="text-purple-300/90 italic text-sm">{msg.interpretedPlayerAction}</p>
                        </div>
                    )}

                    {msg.dialogue && <p className="whitespace-pre-wrap text-gray-300 mt-1">"{msg.dialogue}"</p>}
                    {msg.sfx && <DynamicSfxPlayer sfx={msg.sfx} messageId={msg.id} assetCache={assetCache} />}
                </div>
            )}
        </div>
    );
});

const BgmMoodDisplay: React.FC<{ mood: string }> = ({ mood }) => {
    const { t } = useI18n();
    const moodKey = `game.bgmMood.moods.${mood}`;
    const translatedMood = t(moodKey, { mood });
    return (
        <div className="my-2 p-2 rounded-md bg-gray-900/50 text-center italic text-sm text-indigo-300 flex items-center justify-center gap-2">
           {t('game.bgmMood.change', { mood: translatedMood })}
        </div>
    );
}

const CinematicDisplay: React.FC<{ cinematic: Cinematic; messageId: string; assetCache: Record<string, string>; onGenerateVideoClick: (messageId: string, prompt: string) => void; isBusy: boolean; }> = ({ cinematic, messageId, assetCache, onGenerateVideoClick, isBusy }) => {
    const { t } = useI18n();
    const url = cinematic.assetKey ? assetCache[cinematic.assetKey] : undefined;

    if (url) {
         if (cinematic.type === 'image' || cinematic.type === 'location') return <img src={url} alt={cinematic.prompt} className="mt-2 rounded-lg max-w-full max-h-[45vh] object-contain mx-auto" />;
         else return <video src={url} controls autoPlay muted loop className="mt-2 rounded-lg max-w-full max-h-[45vh] object-contain mx-auto" />;
    }
    switch (cinematic.status) {
        case 'pending': 
        case 'queued':
            if (cinematic.type === 'video') {
                 return (
                    <div className="mt-2 flex flex-col items-center justify-center gap-2 text-white p-4 bg-gray-900/50 rounded-lg">
                       <button onClick={() => onGenerateVideoClick(messageId, cinematic.prompt)} disabled={isBusy} className="bg-indigo-600 font-semibold py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-500 flex items-center gap-2"><VideoIcon className="w-5 h-5" />{t('videoGenerator.generateButton')}</button>
                    </div>);
            }
            return (<div className="mt-2 flex flex-col items-center justify-center gap-2 text-white p-4 bg-gray-900/50 rounded-lg"><ImageIcon className="w-8 h-8 text-gray-500" /><span className="text-sm text-gray-400 italic">Image generation queued...</span></div>);
        case 'loading':
            return (<div className="mt-2 flex flex-col items-center justify-center gap-2 text-white p-4 bg-gray-900/50 rounded-lg"><SmallLoadingSpinner /><span className="text-sm">{cinematic.type === 'image' ? t('game.generatingImage') : t('game.generatingVideo')}</span></div>);
        case 'error': return <p className="mt-2 text-red-400 text-center p-4 bg-red-900/20 rounded-lg">{t('game.mediaError')}</p>;
        default: return null;
    }
};

interface MessageLogProps {
    playerCharacterName: string;
}

const MessageLog: React.FC<MessageLogProps> = ({ playerCharacterName }) => {
  const { t } = useI18n();
  const { 
      gameState, 
      tasks, 
      isBusy,
      changeMusicByMood,
      onPlayTtsRequest,
      playingMessageKey,
      onGenerateVideoClick
  } = useGameContext();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  // FIX: Replaced gameState.messages with gameState.gameLog
  const prevMessagesLength = useRef(gameState.gameLog.length);

  const isPlayerActionPending = tasks.some(t => t.type === 'player-action');
  const isAnyTtsLoading = tasks.some(t => t.type === 'generate-tts' && (t.status === 'in-progress' || (tasks.indexOf(t) === 0 && isPlayerActionPending)));

  useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  // FIX: Replaced gameState.messages with gameState.gameLog
  }, [gameState.gameLog]);

  useEffect(() => {
    // FIX: Replaced gameState.messages with gameState.gameLog
    if (gameState.gameLog.length > prevMessagesLength.current) {
        // FIX: Replaced gameState.messages with gameState.gameLog
        const newMessages = gameState.gameLog.slice(prevMessagesLength.current);
        let lastMood: string | null = null;
        newMessages.forEach(msg => {
            const bgmRegex = /\[BGM_MOOD:([a-zA-Z]+)\]/g;
            const matches = [...(msg.content ?? '').matchAll(bgmRegex)];
            if (matches.length > 0) lastMood = matches[matches.length - 1][1];
        });
        if (lastMood) changeMusicByMood(lastMood);
    }
    // FIX: Replaced gameState.messages with gameState.gameLog
    prevMessagesLength.current = gameState.gameLog.length;
  // FIX: Replaced gameState.messages with gameState.gameLog
  }, [gameState.gameLog, changeMusicByMood]);

  const getAuthorStyle = useCallback((author: string, isGM: boolean) => {
    if (isGM) return "text-yellow-400";
    if (author === playerCharacterName) return "text-green-400";
    return "text-cyan-400";
  }, [playerCharacterName]);

  const getTtsAriaLabel = useCallback((author: string, messageId: string) => {
    if (playingMessageKey === messageId + '-loading') return t('game.ariaLabels.loadingTts', { author });
    if (playingMessageKey === messageId) return t('game.ariaLabels.stopTts', { author });
    return t('game.ariaLabels.playTts', { author });
  }, [playingMessageKey, t]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3 text-sm scrollbar-thin">
      {gameState.gameLog.map((msg, index) => {
          const isLatestPlayerMessage = !msg.isGM && index === gameState.gameLog.length - 1;
          const isPending = isLatestPlayerMessage && isPlayerActionPending;
          return <MemoizedMessageItem
                    key={msg.id}
                    msg={msg}
                    getAuthorStyle={getAuthorStyle}
                    isPending={isPending}
                    isTtsEnabled={gameState.isTtsEnabled}
                    playingMessageKey={playingMessageKey}
                    onPlayTtsRequest={onPlayTtsRequest}
                    getTtsAriaLabel={getTtsAriaLabel}
                    isAnyTtsLoading={isAnyTtsLoading}
                    playerCharacterName={playerCharacterName}
                    cinematic={msg.cinematic}
                    assetCache={gameState.assetCache}
                    onGenerateVideoClick={onGenerateVideoClick}
                    isBusy={isBusy}
                 />;
      })}
       <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageLog;
