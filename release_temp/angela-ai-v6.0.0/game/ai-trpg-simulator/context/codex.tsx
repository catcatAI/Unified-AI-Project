import React, { createContext, useContext, ReactNode, useCallback, useMemo, useState, useEffect } from 'react';
import { GlobalCodex, CodexAsset, GameState, CodexCategory, CodexSaveAsset, CodexCharacterAsset, CodexItemAsset, CodexLocationAsset, CodexImageAsset, CodexVideoAsset, CodexAudioAsset } from '../types';
import { produce } from 'immer';
import { presetCodex } from '../services/presetAssets';
import { cleanGameStateForSave, rehydrateGameState, migrateGameState } from '../services/gameStateService';

// --- localforage setup ---
declare const localforage: any;
if (typeof localforage !== 'undefined') {
    localforage.config({
        driver: [localforage.INDEXEDDB, localforage.WEBSQL, localforage.LOCALSTORAGE],
        name: 'ai-trpg-db',
        storeName: 'codex_store',
        description: 'Storage for AI TRPG Simulator data'
    });
} else {
    console.error("localforage is not loaded. Database will not work.");
}


// --- Codex Context ---
interface CodexContextType {
    codex: GlobalCodex;
    isLoading: boolean;
    addCodexEntry: (asset: CodexAsset) => Promise<void>;
    updateCodexEntry: (asset: Partial<CodexAsset> & { id: string, type: CodexAsset['type'] }) => Promise<void>;
    deleteCodexEntry: (assetId: string, type: CodexCategory) => Promise<void>;
    importFromFile: (file: File) => Promise<number>;
    reconstructSaveAsset: (saveAssetId: string) => Promise<void>;
    getRawCodex: () => GlobalCodex;
    saveGame: (gameState: GameState, saveName: string) => Promise<void>;
    rehydrateGameStateFromCodex: (gameState: GameState) => GameState;
}

const CodexContext = createContext<CodexContextType | undefined>(undefined);

const getCategoryKey = (type: CodexCategory): keyof GlobalCodex => {
    switch (type) {
        case 'audio': return 'audio';
        case 'realEstate': return 'realEstate';
        case 'block': return 'blocks';
        default: return `${type}s` as keyof GlobalCodex;
    }
};

const mergeCodex = (stored: GlobalCodex | null, initial: GlobalCodex): GlobalCodex => {
    return produce(initial, draft => {
        if (!stored) return;
        for (const category of Object.keys(initial) as Array<keyof GlobalCodex>) {
            if (stored[category]) {
                Object.assign(draft[category], stored[category]);
            }
        }
    });
};

/**
 * Iterates through a GameState and adds any referenced assets
 * into a codex draft if they don't already exist. Centralizes asset extraction logic.
 * @param draft The Immer draft of the GlobalCodex.
 * @param gameState The GameState to harvest assets from.
 * @returns The number of new assets added to the codex draft.
 */
const harvestAssetsFromGameState = (draft: GlobalCodex, gameState: GameState): number => {
    let count = 0;
    const assetCache = gameState.assetCache || {};
    const sanitizeId = (name: string) => name.toLowerCase().replace(/\s+/g, '-');

    const addOrUpdateAsset = (categoryKey: keyof GlobalCodex, asset: CodexAsset) => {
        const category = draft[categoryKey] as Record<string, CodexAsset>;
        if (!category[asset.id]) {
            category[asset.id] = asset;
            count++;
        } else if (!category[asset.id].isPreset) {
            Object.assign(category[asset.id], asset);
        }
    };

    Object.entries(assetCache).forEach(([key, url]) => {
        if (!key || !url) return;
        
        if (key.startsWith('portrait-')) {
            const charName = key.replace('portrait-', '');
            const char = gameState.characters.find(c => c.name === charName);
            if (char) {
                const asset: CodexCharacterAsset = { type: 'character', id: sanitizeId(char.name), name: char.name, description: char.description, gender: char.gender, imageUrl: url };
                addOrUpdateAsset('characters', asset);
            }
        } else if (key.startsWith('icon-')) {
            const allItems = [...gameState.partyStash, ...gameState.locationItems, ...gameState.characters.flatMap(c => c.inventory || []), ...gameState.vehicles.flatMap(v => v.inventory || [])];
            const item = allItems.find(i => i.iconAssetKey === key);
            if (item) {
                const asset: CodexItemAsset = { type: 'item', id: sanitizeId(item.name), name: item.name, description: item.description, iconUrl: url };
                addOrUpdateAsset('items', asset);
            }
        } else if (key.startsWith('cinematic-')) {
            const msg = gameState.gameLog.find(m => m.cinematic?.assetKey === key);
            if (msg?.cinematic) {
                const type = msg.cinematic.type === 'video' ? 'video' : 'image';
                const catKey = type === 'video' ? 'videos' : 'images';
                const asset: CodexImageAsset | CodexVideoAsset = { type, id: key, name: msg.cinematic.prompt, description: `Cinematic from game log`, url };
                addOrUpdateAsset(catKey, asset);
            }
        } else if (key.startsWith('sfx-')) {
            const msg = gameState.gameLog.find(m => m.sfx?.assetKey === key);
            if (msg?.sfx) {
                const asset: CodexAudioAsset = { type: 'audio', id: key, name: msg.sfx.prompt, description: `SFX from game log`, url };
                addOrUpdateAsset('audio', asset);
            }
        } else if (key === gameState.mapAssetKey) {
            const asset: CodexImageAsset = { type: 'image', id: key, name: `Map: ${gameState.gameSummary.slice(0, 20)}...`, description: 'World map from saved game', url };
            addOrUpdateAsset('images', asset);
        } else if (key === gameState.locationAssetKey) {
            const asset: CodexLocationAsset = { type: 'location', id: key, name: `Location: ${gameState.location}`, description: `Image of ${gameState.location}`, imageUrl: url };
            addOrUpdateAsset('locations', asset);
        } else {
             if (url.startsWith('data:image/')) { addOrUpdateAsset('images', { type: 'image', id: key, name: key, description: 'Imported image asset', url });
             } else if (url.startsWith('data:video/')) { addOrUpdateAsset('videos', { type: 'video', id: key, name: key, description: 'Imported video asset', url });
             } else if (url.startsWith('data:audio/')) { addOrUpdateAsset('audio', { type: 'audio', id: key, name: key, description: 'Imported audio asset', url }); }
        }
    });
    return count;
};


export const CodexProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [codex, setCodex] = useState<GlobalCodex | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const updateStoredCodex = useCallback(async (updater: (draft: GlobalCodex) => void) => {
        try {
            const currentCodex = await localforage.getItem('ai-trpg-codex');
            const baseState = currentCodex ? mergeCodex(currentCodex as GlobalCodex, presetCodex) : presetCodex;
            const newState = produce(baseState, draft => {
                updater(draft);
            });
            await localforage.setItem('ai-trpg-codex', newState);
            setCodex(newState);
        } catch (error) {
            console.error("Failed to update codex in storage:", error);
            throw error;
        }
    }, []);

    useEffect(() => {
        let isMounted = true;
        const loadInitialCodex = async () => {
            // Create a timeout promise that rejects after 5 seconds
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Database load timed out after 5 seconds.')), 5000)
            );

            try {
                // Race localforage against the timeout
                const storedCodex = await Promise.race([
                    localforage.getItem('ai-trpg-codex'),
                    timeoutPromise
                ]);

                if (isMounted) {
                    const merged = mergeCodex(storedCodex as GlobalCodex | null, presetCodex);
                    setCodex(merged);
                }
            } catch (err) {
                console.error("Failed to load codex (or timed out), using presets.", err);
                if (isMounted) {
                    // Fallback to presets if loading fails or times out
                    setCodex(presetCodex);
                }
            } finally {
                if (isMounted) {
                    // This will now always be called, unblocking the UI.
                    setIsLoading(false);
                }
            }
        };

        loadInitialCodex();
        return () => { isMounted = false; };
    }, []);

    const addCodexEntry = useCallback(async (asset: CodexAsset) => {
        await updateStoredCodex(draft => {
            const category = getCategoryKey(asset.type);
            if (!draft[category]) { (draft as any)[category] = {}; }
            const existingAsset = (draft[category] as any)[asset.id];
            if (!existingAsset) {
                (draft[category] as any)[asset.id] = asset;
            } else {
                 Object.assign(existingAsset, asset);
            }
        });
    }, [updateStoredCodex]);
    
    const updateCodexEntry = useCallback(async (asset: Partial<CodexAsset> & { id: string, type: CodexAsset['type'] }) => {
        await updateStoredCodex(draft => {
            const category = getCategoryKey(asset.type);
             if (draft[category]?.[asset.id]) {
                Object.assign(draft[category][asset.id], asset);
            } else {
                (draft[category] as any)[asset.id] = asset;
            }
        });
    }, [updateStoredCodex]);

    const deleteCodexEntry = useCallback(async (assetId: string, type: CodexCategory) => {
        await updateStoredCodex(draft => {
            const category = getCategoryKey(type);
            if (draft[category]?.[assetId] && !draft[category][assetId].isPreset) {
                delete draft[category][assetId];
            }
        });
    }, [updateStoredCodex]);
    
    const saveGame = useCallback(async (gameState: GameState, saveName: string) => {
        await updateStoredCodex(draft => {
            // Harvest any newly generated assets from the game state into the codex
            harvestAssetsFromGameState(draft, gameState);
    
            // Create the clean save asset
            const cleanState = cleanGameStateForSave(gameState);
            const newSaveAsset: CodexSaveAsset = {
                id: `save-${Date.now()}`,
                type: 'save',
                name: saveName,
                description: `Saved on ${new Date().toLocaleString()}`,
                gameState: cleanState,
                createdAt: new Date().toISOString(),
            };
            draft.saves[newSaveAsset.id] = newSaveAsset;
        });
    }, [updateStoredCodex]);


    const importFromFile = useCallback(async (file: File) => {
        const fileContent = await file.text();
        const data = JSON.parse(fileContent);
        
        let count = 0;
        await updateStoredCodex(draft => {
            let dataToImport: (GameState | Partial<GlobalCodex>)[] = [];
            let isGameState = false;

            if (data.type === 'AITRPG_SAVE' && data.gameState) {
                dataToImport.push(data.gameState); isGameState = true;
            } else if (data.gameState && data.gameState.gamePhase) {
                dataToImport.push(data.gameState); isGameState = true;
            } else if (data.gamePhase) { // Raw game state object
                dataToImport.push(data); isGameState = true;
            } else if (data.type === 'AITRPG_CODEX' || (data.characters && data.items)) {
                dataToImport.push(data);
            } else {
                throw new Error(`Unrecognized file format in ${file.name}.`);
            }
            
            if (isGameState) {
                dataToImport = dataToImport.map(gs => migrateGameState(gs as GameState));
            }

            dataToImport.forEach(d => {
                if ('gamePhase' in d) {
                    const gameState = d as GameState;
                    count += harvestAssetsFromGameState(draft, gameState);

                    const saveId = `save-import-${Date.now()}-${Math.random()}`;
                    const newSaveAsset: CodexSaveAsset = {
                        id: saveId,
                        type: 'save',
                        name: `Imported: ${file.name.replace(/\.json$/, '')}`,
                        description: `Imported on ${new Date().toLocaleDateString()}. Starts: "${gameState.gameLog[0]?.content.substring(0, 40)}..."`,
                        gameState: cleanGameStateForSave(gameState),
                        createdAt: new Date().toISOString(),
                    };
                    draft.saves[newSaveAsset.id] = newSaveAsset;
                    count++;
                } else {
                    const codexData = d as Partial<GlobalCodex> & { type?: string };
                    Object.keys(codexData).forEach(key => {
                        // @fix: The key from a codex import might be 'type', which is not a keyof GlobalCodex.
                        // Check for 'type' before casting to a narrower type to avoid a TypeScript error.
                        if (key === 'type') { // Simplified check, assumes 'type' is not a valid category name
                            return;
                        }
                        const catKey = key as keyof GlobalCodex;
                        const categoryData = codexData[catKey];
                        if (categoryData) {
                            Object.values(categoryData).forEach((asset: any) => {
                                 if (asset && asset.id && asset.type) {
                                     const targetCategory = draft[getCategoryKey(asset.type)] as Record<string, CodexAsset>;
                                     if (targetCategory && !targetCategory[asset.id]) {
                                        targetCategory[asset.id] = asset;
                                        count++;
                                     }
                                 }
                            });
                        }
                    });
                }
            });
        });
        return count;
    }, [updateStoredCodex]);

    const reconstructSaveAsset = useCallback(async (saveAssetId: string) => {
        await updateStoredCodex(draft => {
            const originalAsset = draft.saves[saveAssetId];
            if (!originalAsset) {
                console.error("Save asset to reconstruct not found:", saveAssetId);
                return;
            }
            // 1. Migrate the old format to the new format. This populates a temporary `assetCache`.
            const migratedState = migrateGameState(originalAsset.gameState);
            
            // 2. Harvest assets from the migrated state's temporary cache into the main codex draft.
            harvestAssetsFromGameState(draft, migratedState);

            // 3. Create the new save asset using the cleaned (cacheless) version of the migrated state.
            const newSaveAsset: CodexSaveAsset = {
                id: `save-reconstructed-${Date.now()}`,
                type: 'save',
                name: `${originalAsset.name} (Reconstructed)`,
                description: `Reconstructed on ${new Date().toLocaleString()}`,
                gameState: cleanGameStateForSave(migratedState),
                createdAt: new Date().toISOString(),
            };

            draft.saves[newSaveAsset.id] = newSaveAsset;
        });
    }, [updateStoredCodex]);

    const getRawCodex = useCallback(() => {
        return codex || presetCodex;
    }, [codex]);

    const rehydrateGameStateFromCodex = useCallback((gameState: GameState): GameState => {
        const activeCodex = codex || presetCodex;
        return rehydrateGameState(gameState, activeCodex);
    }, [codex]);


    const value = useMemo(() => ({
        codex: codex!, // The AppContent component handles the loading state.
        isLoading,
        addCodexEntry,
        updateCodexEntry,
        deleteCodexEntry,
        importFromFile,
        getRawCodex,
        saveGame,
        rehydrateGameStateFromCodex,
        reconstructSaveAsset
    }), [codex, isLoading, addCodexEntry, updateCodexEntry, deleteCodexEntry, importFromFile, getRawCodex, saveGame, rehydrateGameStateFromCodex, reconstructSaveAsset]);

    return (
        <CodexContext.Provider value={value}>
            {children}
        </CodexContext.Provider>
    );
};

export const useCodex = (): CodexContextType => {
    const context = useContext(CodexContext);
    if (context === undefined) {
        throw new Error('useCodex must be used within a CodexProvider');
    }
    return context;
};