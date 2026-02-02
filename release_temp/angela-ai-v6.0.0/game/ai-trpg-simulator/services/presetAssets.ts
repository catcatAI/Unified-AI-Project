import { GlobalCodex, CodexCharacterAsset, CodexItemAsset, CodexLocationAsset, CodexAudioAsset } from '../types';
import * as audioAssets from './audioAssets';
import * as characterPresets from '../presets';
import * as visualAssets from '../components/assetData';

// Helper to create a more user-friendly name from a camelCase key
const formatAssetName = (key: string) => {
    return key.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase());
};

const audioDescriptions: Record<string, string> = {
    calmMusic: 'A soothing and calm musical loop, suitable for peaceful exploration or quiet moments.',
    actionMusic: 'An energetic and driving musical loop for action sequences, combat, or high-stakes situations.',
    suspenseMusic: 'A tense and suspenseful musical piece, perfect for building tension or exploring dangerous areas.',
    mysteriousMusic: 'A mysterious and atmospheric track, ideal for investigation or discovering ancient secrets.',
    epicMusic: 'An epic and heroic musical theme for triumphant moments or grand revelations.',
    sadMusic: 'A somber and sad melody for emotional or melancholic scenes.',
    horrorMusic: 'A discordant and unsettling track for horror-themed encounters or frightening environments.'
};

export const presetCodex: GlobalCodex = {
    characters: Object.fromEntries(
        characterPresets.characters
            .filter(char => char.id !== 'custom') // Exclude the 'custom' option
            .map(char => [
            char.id,
            {
                id: char.id,
                type: 'character',
                name: char.titleKey,
                description: char.descriptionKey,
                gender: 'other', // Will be overridden below
                isPreset: true,
            } as CodexCharacterAsset
        ])
    ),
    items: {
        'pistol': { id: 'pistol', type: 'item', name: 'presets.items.pistol.name', description: 'presets.items.pistol.description', iconUrl: visualAssets.pistolIcon, isPreset: true },
        'medkit': { id: 'medkit', type: 'item', name: 'presets.items.medkit.name', description: 'presets.items.medkit.description', iconUrl: visualAssets.medkitIcon, isPreset: true },
        'shotgun': { id: 'shotgun', type: 'item', name: 'presets.items.shotgun.name', description: 'presets.items.shotgun.description', iconUrl: visualAssets.shotgunIcon, isPreset: true },
        'cyber-blade': { id: 'cyber-blade', type: 'item', name: 'presets.items.cyber-blade.name', description: 'presets.items.cyber-blade.description', iconUrl: visualAssets.bladeIcon, isPreset: true },
        'health-potion': { id: 'health-potion', type: 'item', name: 'presets.items.health-potion.name', description: 'presets.items.health-potion.description', iconUrl: visualAssets.potionIcon, isPreset: true },
        'longbow': { id: 'longbow', type: 'item', name: 'presets.items.longbow.name', description: 'presets.items.longbow.description', iconUrl: visualAssets.bowIcon, isPreset: true },
        'rations': { id: 'rations', type: 'item', name: 'presets.items.rations.name', description: 'presets.items.rations.description', iconUrl: visualAssets.rationsIcon, isPreset: true },
        'scanner': { id: 'scanner', type: 'item', name: 'presets.items.scanner.name', description: 'presets.items.scanner.description', iconUrl: visualAssets.scannerIcon, isPreset: true },
    },
    locations: {
        'cyberpunk-map': { id: 'cyberpunk-map', type: 'location', name: 'presets.locations.cyberpunk-map.name', description: 'presets.locations.cyberpunk-map.description', imageUrl: visualAssets.cyberpunkMap, isPreset: true },
        'fantasy-map': { id: 'fantasy-map', type: 'location', name: 'presets.locations.fantasy-map.name', description: 'presets.locations.fantasy-map.description', imageUrl: visualAssets.fantasyMap, isPreset: true },
        'space-map': { id: 'space-map', type: 'location', name: 'presets.locations.space-map.name', description: 'presets.locations.space-map.description', imageUrl: visualAssets.spaceMap, isPreset: true },
        'cyberpunk-location': { id: 'cyberpunk-location', type: 'location', name: 'presets.locations.cyberpunk-location.name', description: 'presets.locations.cyberpunk-location.description', imageUrl: visualAssets.cyberpunkLocation, isPreset: true },
        'fantasy-location': { id: 'fantasy-location', type: 'location', name: 'presets.locations.fantasy-location.name', description: 'presets.locations.fantasy-location.description', imageUrl: visualAssets.fantasyLocation, isPreset: true },
        'space-location': { id: 'space-location', type: 'location', name: 'presets.locations.space-location.name', description: 'presets.locations.space-location.description', imageUrl: visualAssets.spaceLocation, isPreset: true },
    },
    vehicles: {},
    realEstate: {},
    images: {},
    videos: {},
    audio: Object.fromEntries(
        Object.entries(audioAssets).map(([key, url]) => [
            key.toLowerCase(),
            {
                id: key.toLowerCase(),
                type: 'audio',
                name: formatAssetName(key),
                description: audioDescriptions[key] || 'A background music track.',
                url: url as string,
                isPreset: true,
            } as CodexAudioAsset
        ])
    ),
    models: {},
    blocks: {},
    saves: {},
};

// Manual overrides for more specific preset character details
(presetCodex.characters['matsu'] as CodexCharacterAsset).gender = 'female';
(presetCodex.characters['saki'] as CodexCharacterAsset).gender = 'female';
(presetCodex.characters['nova'] as CodexCharacterAsset).gender = 'female';
(presetCodex.characters['kiko'] as CodexCharacterAsset).gender = 'female';
(presetCodex.characters['kaelen'] as CodexCharacterAsset).gender = 'male';
(presetCodex.characters['jax'] as CodexCharacterAsset).gender = 'male';