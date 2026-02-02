import { produce } from 'immer';
import { GameState, Item, InventoryContainer, InventoryAction } from '../types';
import { findInventory } from '../services/inventoryService';

export const inventoryReducer = (draft: GameState, action: InventoryAction) => {
    switch (action.type) {
        case 'MOVE_ITEM': {
            const { from, to, item, quantity } = action.payload;

            // This logic is designed to be atomic within an Immer producer.
            const sourceContainer = findInventory(draft, from);
            if (sourceContainer) {
                const itemIndex = sourceContainer.findIndex(i => i.id === item.id);
                if (itemIndex > -1) {
                    const sourceItem = sourceContainer[itemIndex];
                    const moveQuantity = Math.min(quantity, sourceItem.quantity);
                    
                    const destContainer = findInventory(draft, to);
                    if (destContainer) {
                        // If move is successful, update source. Otherwise, do nothing.
                        const existingDestItem = destContainer.find(i => i.name.toLowerCase() === item.name.toLowerCase());
                        if (existingDestItem) {
                            existingDestItem.quantity += moveQuantity;
                        } else {
                            // Create a new item stack in the destination.
                            destContainer.push({ ...item, quantity: moveQuantity });
                        }

                        // Update source item quantity or remove it.
                        sourceItem.quantity -= moveQuantity;
                        if (sourceItem.quantity <= 0) {
                            sourceContainer.splice(itemIndex, 1);
                        }
                    } else {
                        console.warn("Could not find destination inventory for MOVE_ITEM:", to);
                    }
                } else {
                    console.warn(`Could not find item to move (id: ${item.id}) in source container:`, from);
                }
            } else {
                console.warn("Could not find source inventory for MOVE_ITEM:", from);
            }
            break;
        }
        case 'ADD_ITEM_TO_INVENTORY': {
            const { owner, item } = action.payload;
            const container = findInventory(draft, owner);
            if (container) {
                const existingItem = container.find(i => i.name.toLowerCase() === item.name.toLowerCase());
                if (existingItem) {
                    existingItem.quantity += item.quantity;
                } else {
                    container.push({ ...item, id: `item-turn-${Date.now()}-${Math.random()}` });
                }
            } else {
                console.warn("Could not find inventory container to add item:", owner);
            }
            break;
        }
        case 'REMOVE_ITEM_FROM_INVENTORY': {
            const { owner, item: itemToRemove, quantity } = action.payload;
            const container = findInventory(draft, owner);
            if (container) {
                let itemIndex = -1;
                // Prioritize ID match for precise operations like drag-and-drop
                if (itemToRemove.id) {
                    itemIndex = container.findIndex(i => i.id === itemToRemove.id);
                }
                // Fallback to name match for AI-driven changes
                if (itemIndex === -1) {
                    itemIndex = container.findIndex(i => i.name.toLowerCase() === itemToRemove.name.toLowerCase());
                }

                if (itemIndex > -1) {
                    const currentItem = container[itemIndex];
                    const quantityToRemove = Math.min(quantity, currentItem.quantity);
                    currentItem.quantity -= quantityToRemove;
                    if (currentItem.quantity <= 0) {
                        container.splice(itemIndex, 1);
                    }
                } else {
                     console.warn(`Attempted to remove non-existent item '${itemToRemove.name}' from container.`, owner);
                }
            } else {
                console.warn("Could not find inventory container to remove item:", owner);
            }
            break;
        }
        case 'UPDATE_ITEM_ICON_STATUS': {
            const updateItem = (item: Item) => { 
                if(item.name.toLowerCase() === action.payload.itemName.toLowerCase()) {
                    item.iconStatus = action.payload.status;
                    if(action.payload.assetKey) {
                        item.iconAssetKey = action.payload.assetKey;
                    }
                    if (action.payload.iconUrl && action.payload.assetKey) {
                        draft.assetCache[action.payload.assetKey] = action.payload.iconUrl;
                    }
                }
            };
            draft.characters.forEach(c => c.inventory.forEach(updateItem));
            draft.partyStash.forEach(updateItem);
            draft.locationItems.forEach(updateItem);
            draft.vehicles.forEach(v => v.inventory.forEach(updateItem));
            break;
        }
    }
};
