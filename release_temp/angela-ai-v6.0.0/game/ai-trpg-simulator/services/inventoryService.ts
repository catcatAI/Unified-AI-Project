import { GameState, Item, InventoryContainer } from '../types';
import { produce } from 'immer';

/**
 * Finds and returns a direct reference to an inventory array within the game state.
 * NOTE: This is intended to be used within an Immer produce callback
 * to avoid direct mutation of the state.
 * @param draft The Immer draft of the GameState.
 * @param owner The identifier for the inventory owner.
 * @returns The specific item array, or undefined if not found.
 */
export function findInventory(draft: GameState | ReturnType<typeof produce<GameState, GameState>>, owner: InventoryContainer): Item[] | undefined {
    switch(owner.type) {
        case 'player': {
            const player = draft.characters.find(c => !c.isAI);
            return player?.inventory;
        }
        case 'character': {
            const character = draft.characters.find(c => c.name.toLowerCase() === owner.name.toLowerCase());
            return character?.inventory;
        }
        case 'stash': 
            return draft.partyStash;
        case 'ground': 
            return draft.locationItems;
        case 'vehicle': {
            const vehicle = draft.vehicles.find(v => v.id === owner.id);
            return vehicle?.inventory;
        }
        default:
            return undefined;
    }
}


/**
 * Returns a new GameState with an item added to the specified inventory using Immer.
 * Handles stacking of items with the same name.
 * @param state The original GameState.
 * @param owner The inventory to add to.
 * @param itemToAdd The item to add.
 * @returns A new GameState object with the change applied.
 */
export const addItemToInventory = (state: GameState, owner: InventoryContainer, itemToAdd: Item): GameState => {
    if (!itemToAdd || typeof itemToAdd.name !== 'string' || typeof itemToAdd.quantity !== 'number') {
        console.warn("addItemToInventory called with invalid item:", itemToAdd);
        return state;
    }

    return produce(state, draft => {
        const container = findInventory(draft, owner);

        if (container) {
            const existingItem = container.find(i => i.name.toLowerCase() === itemToAdd.name.toLowerCase());
            if (existingItem) {
                existingItem.quantity += itemToAdd.quantity;
            } else {
                container.push({ ...itemToAdd, id: `item-${Date.now()}-${Math.random()}` });
            }
        } else {
            console.warn("Could not find inventory container to add item:", owner);
        }
    });
};

/**
 * Returns a new GameState with an item removed from the specified inventory using Immer.
 * @param state The original GameState.
 * @param owner The inventory to remove from.
 * @param itemToRemove The item to remove (matching by ID).
 * @param quantity The amount to remove.
 * @returns A new GameState object with the change applied.
 */
export const removeItemFromInventory = (state: GameState, owner: InventoryContainer, itemToRemove: Item, quantity: number): GameState => {
    if (!itemToRemove || typeof itemToRemove.id !== 'string') {
        console.warn("removeItemFromInventory called with invalid item:", itemToRemove);
        return state;
    }
    
    return produce(state, draft => {
        const container = findInventory(draft, owner);
        
        if (container) {
            const itemIndex = container.findIndex(i => i.id === itemToRemove.id);
            if (itemIndex > -1) {
                const currentItem = container[itemIndex];
                const moveQuantity = Math.min(quantity, currentItem.quantity);
                currentItem.quantity -= moveQuantity;
                if (currentItem.quantity <= 0) {
                    container.splice(itemIndex, 1);
                }
            }
        } else {
            console.warn("Could not find inventory container to remove item:", owner);
        }
    });
};