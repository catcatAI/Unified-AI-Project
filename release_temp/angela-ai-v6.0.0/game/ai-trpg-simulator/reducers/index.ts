import { produce } from 'immer';
import { GameState, GamePhase, PlayerActionSuccessResult, CombinedTrpgGameAction, CharactersAction, InventoryAction, MapAction, GameLogAction, MiscAction } from '../types';
import { charactersReducer } from './charactersReducer';
import { inventoryReducer } from './inventoryReducer';
import { mapReducer } from './mapReducer';
import { gameLogReducer } from './gameLogReducer';
import { miscReducer } from './miscReducer';
import { processAiTurn } from '../services/gameStateService';

// Initial state for the game
export const initialGameState: GameState = {
    gamePhase: GamePhase.SETUP,
    locale: 'zh',
    difficulty: { preset: 'normal', showAiParty: true, enableVehicles: true, enableRealEstate: false, followPlot: true },
    characters: [], partyStash: [], locationItems: [], vehicles: [], realEstate: [],
    gameLog: [], gameLogSummary: '', genreAndTone: '', gameSummary: '', isTtsEnabled: true, location: "Unknown",
    mapImagePrompt: '', 
    locationImagePrompt: '', 
    assetCache: {}, gameMode: 'narrative', gameStyle: 'narrative', activeEnemies: [], resources: {}, knownLocations: [],
    initiativeOrder: [],
    currentInitiativeIndex: 0,
    map: null, 
    isFallbackActive: false,
    cognitiveState: {
        vdafScore: 0,
        activeMCore: 'IDLE',
        chaosFactor: 0,
    },
    suggestedActions: [],
    craftingIngredients: [],
};

export const rootReducer = (state: GameState = initialGameState, action: CombinedTrpgGameAction): GameState => {
    return produce(state, draft => {
        switch (action.type) {
            case 'START_GAME': {
                // This action now fully replaces the state, becoming the source of truth for a new/loaded game.
                const newGameState = action.payload.gameState;
                Object.assign(draft, newGameState);
                // Ensure phase is correctly set to playing when starting/loading.
                draft.gamePhase = GamePhase.PLAYING;
                // Ensure initiative is set correctly for the new party
                const player = newGameState.characters.find(c => !c.isAI);
                const aiParty = newGameState.characters.filter(c => c.isAI);
                draft.initiativeOrder = player ? [player.name, ...aiParty.map(c => c.name)] : aiParty.map(c => c.name);
                draft.currentInitiativeIndex = 0;
                break;
            }
             case 'POPULATE_GENERATED_DATA': {
                // This action populates the state from the setup screen without changing phase.
                const { gameState } = action.payload;
                Object.assign(draft, gameState);
                draft.gamePhase = GamePhase.SETUP; // Ensure we stay in setup for the review step
                const player = gameState.characters.find(c => !c.isAI);
                const aiParty = gameState.characters.filter(c => c.isAI);
                draft.initiativeOrder = player ? [player.name, ...aiParty.map(c => c.name)] : aiParty.map(c => c.name);
                draft.currentInitiativeIndex = 0;
                break;
            }
            case 'RESTORE_GAME_STATE':
                // Directly replace the draft state with the payload state.
                // This is the core of the rollback functionality.
                return action.payload;

            case 'RESTART_GAME':
                // Reset to initial state but preserve user settings like locale
                return {
                    ...initialGameState,
                    locale: draft.locale, 
                    isTtsEnabled: draft.isTtsEnabled, 
                };
            
            case 'PROCESS_AI_RESPONSE':
                // The entire complex logic is now handled by the gameStateService.
                // The reducer's job is just to call it with the draft state.
                processAiTurn(draft, action.payload);
                break;

            case 'UPDATE_COGNITIVE_STATE':
                draft.cognitiveState = { ...draft.cognitiveState, ...action.payload };
                break;
                
            case 'SET_SUGGESTED_ACTIONS':
                draft.suggestedActions = action.payload;
                break;

            case 'ADD_CRAFTING_INGREDIENT':
                // Simple logic, can stay here.
                draft.craftingIngredients.push(action.payload);
                break;

            case 'REMOVE_CRAFTING_INGREDIENT':
                const indexToRemove = draft.craftingIngredients.findIndex(i => i.id === action.payload.itemId);
                if (indexToRemove > -1) {
                    draft.craftingIngredients.splice(indexToRemove, 1);
                }
                break;

            case 'CLEAR_CRAFTING_INGREDIENTS':
                draft.craftingIngredients = [];
                break;

            // This case is now handled by the miscReducer
            // case 'SET_GAME_PHASE':
            //     draft.gamePhase = action.payload;
            //     break;
            
            default:
                // This pattern allows sub-reducers to be called for their specific actions
                // The `produce` function ensures immutability is handled correctly
                charactersReducer(draft, action as CharactersAction);
                inventoryReducer(draft, action as InventoryAction);
                mapReducer(draft, action as MapAction);
                gameLogReducer(draft, action as GameLogAction);
                miscReducer(draft, action as MiscAction);
                break;
        }
    });
};