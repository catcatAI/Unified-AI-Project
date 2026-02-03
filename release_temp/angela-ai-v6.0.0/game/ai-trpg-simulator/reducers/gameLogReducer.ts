import { produce } from 'immer';
import { GameState, Message, PlayerAction, DiceRoll, Cinematic, Sfx, GameLogAction } from '../types';

export const gameLogReducer = (draft: GameState, action: GameLogAction) => {
    switch (action.type) {
        case 'ADD_PLAYER_MESSAGE_TO_LOG': {
            const playerAction = action.payload.action;
            let content: string;
            if (typeof playerAction === 'string') {
                content = playerAction;
            } else if (playerAction.type === 'move') {
                content = `Move ${playerAction.direction}`;
            } else { // type is 'action'
                content = `Action: ${playerAction.button}`;
            }
            draft.gameLog.push({ id: `msg-player-${Date.now()}`, author: action.payload.author, content, isGM: false, playerAction: playerAction });
            break;
        }
        case 'ADD_GM_NARRATIVE_TO_LOG': {
            const { id, gmName, content, cinematic, sfx } = action.payload;
            draft.gameLog.push({ id, author: gmName, content, isGM: true, cinematic, sfx });
            break;
        }
        case 'ADD_AI_ACTION_TO_LOG': {
            const { id, characterName, action: aiActionContent, dialogue } = action.payload;
            draft.gameLog.push({ id, author: characterName, content: aiActionContent, dialogue, isGM: false });
            break;
        }
        case 'ADD_SYSTEM_MESSAGE_TO_LOG': {
            const { id, content, diceRoll } = action.payload;
            draft.gameLog.push({ id, author: 'System', content, isGM: true, diceRoll });
            break;
        }
        case 'UPDATE_LAST_PLAYER_MESSAGE_INTERPRETATION': {
            for (let i = draft.gameLog.length - 1; i >= 0; i--) {
                const msg = draft.gameLog[i];
                const authorChar = draft.characters.find(c => c.name === msg.author);
                if (!msg.isGM && authorChar && !authorChar.isAI) {
                    msg.interpretedPlayerAction = action.payload;
                    break;
                }
            }
            break;
        }
        case 'UPDATE_CINEMATIC_STATUS': {
            const msg = draft.gameLog.find(m => m.id === action.payload.messageId);
            if (msg?.cinematic) {
                msg.cinematic.status = action.payload.status;
                if (action.payload.assetKey) {
                   msg.cinematic.assetKey = action.payload.assetKey;
                }
                if (action.payload.url && action.payload.assetKey) {
                   draft.assetCache[action.payload.assetKey] = action.payload.url;
                }
            }
            break;
        }
        case 'UPDATE_SFX_STATUS': {
            const msg = draft.gameLog.find(m => m.id === action.payload.messageId);
            if (msg?.sfx) {
                msg.sfx.status = action.payload.status;
                if (action.payload.assetKey) {
                    msg.sfx.assetKey = action.payload.assetKey;
                }
                if (action.payload.url && action.payload.assetKey) {
                    draft.assetCache[action.payload.assetKey] = action.payload.url;
                }
            }
            break;
        }
        case 'SET_GAME_LOG_SUMMARY':
            draft.gameLogSummary = action.payload;
            break;
    }
};
