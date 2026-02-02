export type Task =
  | GenerateSetupTask
  | GenerateSummaryTask
  | GenerateScenarioSuggestionTask
  | GenerateActionSuggestionsTask
  | PlayerActionTask
  | GeneratePortraitTask
  | GenerateIconTask
  | GenerateSfxTask
  | GenerateImageTask
  | GenerateVideoTask
  | GenerateCinematicTask
  | LoadGameTask
  | GenerateMapImageTask
  | GenerateLocationImageTask
  | GenerateTtsTask
  | GenerateThreeViewTask
  | RefineThreeViewTask
  | GenerateThreeViewFromImageTask
  | DescribeImageTask
  | TranscribeAudioTask
  | GenerateSfxFromAudioTask
  | GenerateMusicFromTextTask
  | GeneratePlayerAutoActionTask
  | GenerateMusicFromAudioTask;

// --- Core Game State ---
export enum GamePhase {
  SETUP = 'setup',
  PLAYING = 'playing',
  ERROR = 'error',
}

export type GameStyle = 'narrative' | 'sandbox';
export type GameMode = 'narrative' | 'action' | 'simulation' | 'puzzle';

export interface CharacterStats {
  maxHp: number;
  hp: number;
  maxMp: number;
  mp: number;
  maxStamina: number;
  stamina: number;
  strength: number;
  agility: number;
  intelligence: number;
  // M-Value Stats
  m3LogicStress?: number;
  maxM3LogicStress?: number;
  m6SecurityShield?: number;
  maxM6SecurityShield?: number;
}

export type MValue = 'M1' | 'M2' | 'M3' | 'M4' | 'M5' | 'M6';

export type CharacterGender = 'male' | 'female' | 'other';
export type PortraitStatus = 'pending' | 'queued' | 'loading' | 'done' | 'error';
export interface Character {
  name: string;
  description: string;
  gender: CharacterGender;
  isAI: boolean;
  stats: CharacterStats;
  inventory: Item[];
  mValueProfile?: MValue[];
  portraitAssetKey?: string; // Replaces imageUrl
  portraitStatus?: PortraitStatus;
}

export interface Enemy {
  name: string;
  hp: number;
  maxHp: number;
  description?: string;
}

export type ItemIconStatus = 'pending' | 'queued' | 'loading' | 'done' | 'error';
export interface Item {
  id: string;
  name: string;
  description: string;
  quantity: number;
  mValueProfile?: MValue[];
  iconGenerationPrompt?: string; // Prompt for generating the item's icon
  iconAssetKey?: string; // Replaces iconUrl
  iconStatus?: ItemIconStatus;
}

export interface Vehicle {
  id: string;
  name: string;
  description: string;
  inventory: Item[];
}

export interface RealEstate {
    id: string;
    name: string;
    description: string;
}

export type InventoryContainer =
  | { type: 'player' }
  | { type: 'character'; name: string }
  | { type: 'stash' }
  | { type: 'ground' }
  | { type: 'vehicle'; id: string };

export interface DiceRoll {
    characterName: string;
    targetName: string; // The enemy or character being targeted
    action: string;
    roll: string; // e.g., "1d20+3"
    result: number;
    successLevel: 'critical_failure' | 'failure' | 'success' | 'critical_success';
}

export type CinematicStatus = 'pending' | 'queued' | 'loading' | 'done' | 'error';
export interface Cinematic {
    type: 'image' | 'video' | 'location';
    prompt: string;
    status: CinematicStatus;
    assetKey?: string; // Replaces url
}

export type SfxStatus = 'pending' | 'queued' | 'loading' | 'done' | 'error';
export interface Sfx {
    prompt: string;
    status: SfxStatus;
    assetKey?: string; // Replaces url
}

export type PlayerAction = string | { type: 'move'; direction: 'up' | 'down' | 'left' | 'right'; } | { type: 'action'; button: 'A' | 'B'; };

export interface MValMapObject {
    id: string;
    name: string;
    x: number;
    y: number;
    icon: string; // Can be emoji or image data URL
}

export interface SandboxMap {
    currentMap: string;
    width: number;
    height: number;
    tiles: string[][]; // 2D array of tile types
    playerX: number;
    playerY: number;
    playerDirection: 'up' | 'down' | 'left' | 'right';
    objects: MValMapObject[]; // NPCs, items, interactables on the map
}


export interface Message {
  id: string;
  author: string;
  content: string; // Narrative or AI action description
  dialogue?: string; // Explicit dialogue for TTS
  isGM: boolean;
  playerAction?: PlayerAction; // Original structured player action for AI interpretation
  interpretedPlayerAction?: string; // GM's interpretation of player's action
  diceRoll?: DiceRoll;
  cinematic?: Cinematic;
  sfx?: Sfx;
}

export type DifficultyPreset = 'easy' | 'normal' | 'hard' | 'custom';
export interface DifficultySettings {
    preset: DifficultyPreset;
    showAiParty: boolean;
    enableVehicles: boolean;
    enableRealEstate: boolean;
    followPlot: boolean;
}

export interface CognitiveState {
    vdafScore: number;
    activeMCore: 'M1' | 'M3' | 'M6' | 'IDLE';
    chaosFactor: number; // 0 to 1
}

export interface GameState {
  gamePhase: GamePhase;
  locale: 'en' | 'zh';
  difficulty: DifficultySettings;
  characters: Character[];
  partyStash: Item[];
  locationItems: Item[]; // Items on the ground in the current location
  vehicles: Vehicle[];
  realEstate: RealEstate[];
  gameLog: Message[];
  gameLogSummary: string; // AI generated summary of the game so far
  genreAndTone: string;
  gameSummary: string;
  location: string;
  mapImagePrompt: string; // Prompt used to generate the world map
  locationImagePrompt: string; // Prompt used to generate the current location image
  assetCache: Record<string, string>; // { 'portrait-Kaelen': 'data:image/jpeg;base64,...' }
  isFallbackActive: boolean; // True if using fallback models
  isTtsEnabled: boolean; // Current TTS setting, synced from global settings
  gameMode: GameMode;
  gameStyle: GameStyle;
  activeEnemies: Enemy[]; // For action mode
  resources: Record<string, number>; // For simulation mode
  knownLocations: { id: string; name: string; description: string; }[]; // Player's known travel locations
  initiativeOrder: string[]; // Character names in initiative order
  currentInitiativeIndex: number; // Index of the character whose turn it is
  map: SandboxMap | null; // For sandbox mode
  mapAssetKey?: string; // Replaces mapImageUrl
  locationAssetKey?: string; // Replaces locationImageUrl
  cognitiveState: CognitiveState;
  suggestedActions: string[];
  craftingIngredients: Item[];
}

// --- General Settings ---
export interface Settings {
  locale: 'en' | 'zh';
  bgmVolume: number;
  sfxVolume: number;
  enablePortraits: boolean;
  enableTts: boolean;
  enableMapImages: boolean;
  enableItemIcons: boolean;
  enableLocationImages: boolean;
  enableSfx: boolean;
  enableVoiceInput: boolean;
  followPlot: boolean; // For difficulty setting
  primaryTextModel: string;
  fallbackTextModel: string;
  imageModel: string; // Primary image generation model (e.g., Imagen)
  imageEditModel: string; // Image editing/fast image generation model (e.g., Gemini Flash Image)
  videoModel: string; // Video generation model (e.g., Veo)
  sfxModel: string; // Sound effect generation model
  ttsModel: string; // Text-to-speech model
  musicModel: string; // Music generation model
  aiCreativity: number; // Temperature for AI models
  qteDifficulty: 'easy' | 'normal' | 'hard';
  disableQteTimer: boolean;
  enableMvalGen: boolean; // Feature flag for M-VAL generation tools
  roundRobinInitiative: boolean; // New setting
  characterAgency: boolean; // New setting
  enableDragAndDrop: boolean; // New setting
}


// --- API Task Types ---
export type ApiSettings = Pick<Settings, 'primaryTextModel' | 'fallbackTextModel' | 'imageModel' | 'imageEditModel' | 'videoModel' | 'sfxModel' | 'ttsModel' | 'musicModel' | 'enableItemIcons' | 'enablePortraits' | 'enableMapImages' | 'enableLocationImages' | 'enableSfx' | 'qteDifficulty' | 'disableQteTimer' | 'roundRobinInitiative' | 'characterAgency' | 'aiCreativity'>;


export type TaskStatus = 'queued' | 'in-progress' | 'done' | 'error';
interface BaseTask {
  type: string;
  id: string;
  description: string;
  status: TaskStatus;
  priority: number; // Higher number means higher priority (e.g., 10 for setup, 30 for portraits)
  onSuccess?: (result: any) => void;
  onError?: (error: Error) => void;
}

export interface GenerateSetupTask extends BaseTask {
  type: 'generate-setup';
  prompt: string;
  gameStyle: GameStyle;
  aiCount: number;
  difficulty: DifficultySettings;
  locale: 'en' | 'zh';
  temperature: number;
  settings: ApiSettings;
  playerCodexAsset?: CodexAsset;
  aiCodexAssets?: CodexAsset[];
  onFallback: () => void;
  onSuccess?: (result: { playerCharacter: Character; aiCharacters: Character[]; openingScene: string; gameSummary: string; genreAndTone: string; startingLocation: string; suggestedActions: string[]; partyStash?: Item[]; vehicles?: Vehicle[]; realEstate?: RealEstate[]; locationItems?: Item[]; knownLocations?: {id:string, name:string, description:string}[]; mapImagePrompt?: string; locationImagePrompt?: string; map?: SandboxMap; }) => void;
}

export interface GenerateSummaryTask extends BaseTask {
    type: 'generate-summary';
    textToSummarize: string;
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>;
    onFallback: () => void;
    onSuccess?: (summary: string) => void;
}

export interface GenerateScenarioSuggestionTask extends BaseTask {
    type: 'generate-scenario-suggestion';
    currentPrompt: string;
    locale: 'en' | 'zh';
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>;
    onFallback: () => void;
    onSuccess?: (suggestion: string) => void;
}

export interface GenerateActionSuggestionsTask extends BaseTask {
    type: 'generate-action-suggestions';
    gameLog: Message[];
    locale: 'en' | 'zh';
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>;
    onFallback: () => void;
    onSuccess?: (result: { suggestedActions: string[] }) => void;
}

export interface GeneratePlayerAutoActionTask extends BaseTask {
    type: 'generate-player-auto-action';
    gameState: GameState;
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel' | 'aiCreativity'>;
    onFallback: () => void;
    onSuccess?: (action: string) => void;
}

// --- Player Action Result Types ---
export interface StatChange {
    characterName: string;
    stat: keyof CharacterStats;
    change: number; // Can be positive or negative
}

export interface InventoryChange {
    type: 'add' | 'remove';
    target: InventoryContainer | string; // string for legacy compatibility if AI messes up
    item: Item;
}

export interface CharacterChange {
    type: 'add' | 'remove';
    character: Omit<Character, 'isAI' | 'portraitStatus' | 'portraitAssetKey'>; // AI returns core character data
}

export interface VehicleChange {
    type: 'add' | 'remove';
    vehicle: Vehicle;
}

export interface RealEstateChange {
    type: 'add' | 'remove';
    property: RealEstate;
}

export interface KnownLocation {
    id: string;
    name: string;
    description: string;
}

export interface TileChange {
    x: number;
    y: number;
    tile: string;
}

export interface MapObjectChange {
    type: 'add' | 'remove';
    object: MValMapObject;
}

export interface SummonChallenge {
    sequence: string[];
    timeLimit: number; // in seconds
}

export type PlayerActionSuccessResult = {
  newGameLogSummary: string;
  interpretedPlayerAction?: string;
  aiActions: { characterName: string; action: string; dialogue?: string; }[];
  gmNarrative: string;
  diceRoll?: DiceRoll;
  statChanges?: StatChange[];
  inventoryChanges?: InventoryChange[];
  characterChanges?: CharacterChange[];
  vehicleChanges?: VehicleChange[];
  realEstateChanges?: RealEstateChange[];
  knownLocations?: KnownLocation[];
  location?: string;
  gameMode?: GameMode;
  activeEnemies?: Enemy[];
  resources?: { resourceName: string; quantity: number; }[];
  suggestedActions?: string[];
  summonChallenge?: SummonChallenge;
  tile_changes?: TileChange[];
  map_object_changes?: MapObjectChange[];
  m2ChaosNarrative?: string; // M2 Chaos Injection
};

export interface PlayerActionTask extends BaseTask {
  type: 'player-action';
  action: PlayerAction;
  gameState: GameState;
  attachedAsset?: CodexAsset;
  settings: ApiSettings;
  onFallback: () => void;
  onSuccess?: (result: { turnResult: PlayerActionSuccessResult } & CognitiveState) => void;
}

export interface GeneratePortraitTask extends BaseTask {
  type: 'generate-portrait';
  character: Character;
  prompt: string;
  model: string; // The specific image model to use
  onSuccess?: (imageUrl: string) => void;
}

export interface GenerateIconTask extends BaseTask {
  type: 'generate-icon';
  itemName: string;
  prompt: string;
  model: string; // The specific image model to use
  onSuccess?: (iconUrl: string) => void;
}

export interface GenerateSfxTask extends BaseTask {
  type: 'generate-sfx';
  messageId: string;
  prompt: string;
  model: string; // The specific SFX model to use
  onSuccess?: (audioUrl: string) => void;
}

export interface GenerateImageTask extends BaseTask {
    type: 'generate-image';
    prompt: string;
    aspectRatio: '16:9' | '1:1';
    model: string; // The specific image model to use
    sourceImageUrl?: string; // Optional: for image editing tasks
    onSuccess?: (imageUrl: string) => void;
}

export interface GenerateVideoTask extends BaseTask {
    type: 'generate-video';
    prompt: string;
    model: string; // The specific video model to use
    sourceImageUrl?: string; // Optional: for video from image tasks
    lastFrameUrl?: string; // Optional: for video extension with a last frame
    onSuccess?: (videoUrl: string) => void;
}

export interface GenerateCinematicTask extends BaseTask {
    type: 'generate-cinematic'; // Can result in image or video based on prompt/model
    messageId: string;
    prompt: string;
    model: string; // The specific model to use (image or video)
    onSuccess?: (url: string) => void;
}

export interface LoadGameTask extends BaseTask {
  type: 'load-game';
  fileContent: string;
  onSuccess?: (result: { gameState: GameState | any }) => void; // Allow 'any' for migration
}

export interface GenerateMapImageTask extends BaseTask {
    type: 'generate-map-image';
    prompt: string;
    model: string; // The specific image model to use
    onSuccess?: (imageUrl: string) => void;
}

export interface GenerateLocationImageTask extends BaseTask {
    type: 'generate-location-image';
    prompt: string;
    model: string; // The specific image model to use
    onSuccess?: (imageUrl: string) => void;
}

export interface GenerateTtsTask extends BaseTask {
    type: 'generate-tts';
    message: Message;
    character?: Character;
    model: string; // The specific TTS model to use
    onSuccess?: (result: { messageId: string; base64Audio: string }) => void;
}

export type OrthographicView = 'front' | 'side' | 'top';
export interface GenerateThreeViewTask extends BaseTask {
    type: 'generate-three-view';
    prompt: string;
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel' | 'imageModel'>;
    onFallback: () => void;
    onBlueprintGenerated?: (blueprint: string) => void;
    onViewGenerated?: (view: OrthographicView, imageUrl: string) => void;
    onSuccess?: (result: { frontViewUrl: string; sideViewUrl: string; topViewUrl: string }) => void;
}

export interface RefineThreeViewTask extends BaseTask {
    type: 'refine-three-view';
    prompt: string; // Original prompt or latest blueprint
    frontViewUrl: string;
    sideViewUrl: string;
    topViewUrl: string;
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel' | 'imageModel'>;
    onFallback: () => void;
    onBlueprintGenerated?: (blueprint: string) => void;
    onViewGenerated?: (view: OrthographicView, imageUrl: string) => void;
    onSuccess?: (result: { frontViewUrl: string; sideViewUrl: string; topViewUrl: string }) => void;
}

export interface GenerateThreeViewFromImageTask extends BaseTask {
    type: 'generate-three-view-from-image';
    prompt: string; // Description of the object
    sourceImageUrl: string;
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel' | 'imageModel'>;
    onFallback: () => void;
    onBlueprintGenerated?: (blueprint: string) => void;
    onViewGenerated?: (view: OrthographicView, imageUrl: string) => void;
    onSuccess?: (result: { frontViewUrl: string; sideViewUrl: string; topViewUrl: string }) => void;
}

export interface DescribeImageTask extends BaseTask {
    type: 'describe-image';
    sourceImageUrl: string;
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>;
    onFallback: () => void;
    onSuccess?: (description: string) => void;
}

export interface TranscribeAudioTask extends BaseTask {
    type: 'transcribe-audio';
    sourceAudioUrl: string;
    onSuccess?: (transcription: string) => void;
}

export interface GenerateSfxFromAudioTask extends BaseTask {
    type: 'generate-sfx-from-audio';
    sourceAudioUrl: string;
    prompt: string;
    model: string; // Specific SFX model
    onSuccess?: (audioUrl: string) => void;
}

export interface GenerateMusicFromTextTask extends BaseTask {
    type: 'generate-music-from-text';
    prompt: string;
    model: string; // Specific music model
    onSuccess?: (audioUrl: string) => void;
}

export interface GenerateMusicFromAudioTask extends BaseTask {
    type: 'generate-music-from-audio';
    sourceAudioUrl: string;
    prompt: string;
    model: string; // Specific music model
    onSuccess?: (audioUrl: string) => void;
}


// --- Codex Types ---
export type CodexCategory = 'character' | 'item' | 'block' | 'location' | 'vehicle' | 'realEstate' | 'image' | 'video' | 'audio' | 'model' | 'save';

// Base for all Codex Assets
interface BaseCodexAsset {
    id: string;
    type: CodexCategory;
    name: string;
    description: string;
    isPreset?: boolean; // True if it's a built-in preset asset
}

// Specific asset types extending BaseCodexAsset
export interface CodexCharacterAsset extends BaseCodexAsset {
    type: 'character';
    gender: CharacterGender;
    imageUrl?: string;
    portraitGenerationPrompt?: string;
}

export interface CodexItemAsset extends BaseCodexAsset {
    type: 'item' | 'block';
    iconUrl?: string;
    iconGenerationPrompt?: string;
}

export interface CodexLocationAsset extends BaseCodexAsset {
    type: 'location';
    imageUrl?: string;
    imageGenerationPrompt?: string;
}

export interface CodexVehicleAsset extends BaseCodexAsset {
    type: 'vehicle';
    // Add vehicle-specific properties if needed for display in Codex
}

export interface CodexRealEstateAsset extends BaseCodexAsset {
    type: 'realEstate';
    // Add real estate-specific properties if needed for display in Codex
}

export interface CodexImageAsset extends BaseCodexAsset {
    type: 'image';
    url: string; // Base64 or external URL
}

export interface CodexVideoAsset extends BaseCodexAsset {
    type: 'video';
    url: string; // Base64 or external URL
}

export interface CodexAudioAsset extends BaseCodexAsset {
    type: 'audio';
    url: string; // Base64 or external URL
}

export interface CodexModelAsset extends BaseCodexAsset {
    type: 'model';
    frontViewUrl?: string;
    sideViewUrl?: string;
    topViewUrl?: string;
    blueprint?: string; // Text description
}

export interface CodexSaveAsset extends BaseCodexAsset {
    type: 'save';
    gameState: GameState;
    createdAt: string; // ISO string
}

// Union type for all possible Codex assets
export type CodexAsset =
    | CodexCharacterAsset
    | CodexItemAsset
    | CodexLocationAsset
    | CodexVehicleAsset
    | CodexRealEstateAsset
    | CodexImageAsset
    | CodexVideoAsset
    | CodexAudioAsset
    | CodexModelAsset
    | CodexSaveAsset;

// Structure for the entire Codex
export interface GlobalCodex {
    characters: Record<string, CodexCharacterAsset>;
    items: Record<string, CodexItemAsset>;
    blocks: Record<string, CodexItemAsset>; // Blocks are essentially items in sandbox mode
    locations: Record<string, CodexLocationAsset>;
    vehicles: Record<string, CodexVehicleAsset>;
    realEstate: Record<string, CodexRealEstateAsset>;
    images: Record<string, CodexImageAsset>;
    videos: Record<string, CodexVideoAsset>;
    audio: Record<string, CodexAudioAsset>;
    models: Record<string, CodexModelAsset>;
    saves: Record<string, CodexSaveAsset>;
}

// --- UI/Framework Generation Types ---
export type GameGenre = 'adventure' | 'action' | 'simulation' | 'puzzle';

export interface AdventureState {
    narrative: string;
    choices: string[];
}

export interface ActionState {
    narrative: string;
    playerHP: number;
    enemyHP: number;
    choices: string[];
}

export interface SimulationState {
    narrative: string;
    resources: Record<string, number>;
    choices: string[];
}

export interface PuzzleState {
    narrative: string;
    choices: string[];
}

export interface FrameworkTask extends BaseTask {
    type: 'generate-framework';
    prompt: string;
    genre: GameGenre;
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>;
    onFallback: () => void;
    onSuccess?: (result: AdventureState | ActionState | SimulationState | PuzzleState) => void;
}

// --- M-VAL specific asset types ---
export interface MValAssetManifest {
    id: string;
    type: 'character' | 'item' | 'location';
    nameKey: string; // i18n key for the asset's name
    descriptionKey: string; // i18n key for the asset's description
    imagePromptKey?: string; // i18n key for the image generation prompt
}

// --- Toast Notifications ---
export interface Toast {
    id: number;
    message: string;
    type: 'success' | 'info' | 'error';
}

// --- Preset Option ---
export interface PresetOption {
    id: string;
    titleKey: string; // i18n key for title
    descriptionKey: string; // i18n key for description
}

// --- Reducer Actions ---
// Actions handled by charactersReducer
export type CharactersAction =
    | { type: 'ADD_CHARACTER'; payload: Character }
    | { type: 'REMOVE_CHARACTER'; payload: { name: string } }
    | { type: 'UPDATE_CHARACTER_PORTRAIT_STATUS'; payload: { charName: string; status: Character['portraitStatus']; imageUrl?: string, assetKey?: string } }
    | { type: 'UPDATE_CHARACTER_STATS'; payload: { charName: string; stat: keyof CharacterStats; change: number } }
    | { type: 'SET_INITIATIVE_ORDER'; payload: string[] }
    | { type: 'SET_CURRENT_INITIATIVE_INDEX'; payload: number };

// Actions handled by inventoryReducer
export type InventoryAction =
    | { type: 'MOVE_ITEM'; payload: { item: Item; quantity: number; from: InventoryContainer; to: InventoryContainer } }
    | { type: 'ADD_ITEM_TO_INVENTORY'; payload: { owner: InventoryContainer; item: Item } }
    | { type: 'REMOVE_ITEM_FROM_INVENTORY'; payload: { owner: InventoryContainer; item: Item; quantity: number } }
    | { type: 'UPDATE_ITEM_ICON_STATUS'; payload: { itemName: string; status: Item['iconStatus']; iconUrl?: string, assetKey?: string } };

// Actions handled by mapReducer
export type MapAction =
    | { type: 'SET_MAP_ASSET'; payload: { key: string, url: string } }
    | { type: 'SET_LOCATION_ASSET'; payload: { key: string, url: string } }
    | { type: 'SET_MAP_IMAGE_URL'; payload: { key: string; url: string } } // Legacy/Alias for refactor
    | { type: 'SET_LOCATION_IMAGE_URL'; payload: { key: string; url: string } } // Legacy/Alias for refactor
    | { type: 'UPDATE_MAP_TILE'; payload: { x: number; y: number; tile: string } }
    | { type: 'ADD_MAP_OBJECT'; payload: MValMapObject }
    | { type: 'REMOVE_MAP_OBJECT'; payload: { id: string } }
    | { type: 'SANDBOX_MOVE_PLAYER'; payload: { x: number; y: number; direction: 'up' | 'down' | 'left' | 'right' } }
    | { type: 'SANDBOX_SET_PLAYER_DIRECTION'; payload: 'up' | 'down' | 'left' | 'right' }
    | { type: 'SANDBOX_DIG_TILE'; payload: { x: number; y: number; block: Item } }
    | { type: 'SET_MAP_DATA'; payload: GameState['map'] };

// Actions handled by gameLogReducer
export type GameLogAction =
    | { type: 'ADD_PLAYER_MESSAGE_TO_LOG'; payload: { action: PlayerAction; author: string } }
    | { type: 'ADD_GM_NARRATIVE_TO_LOG'; payload: { id: string, gmName: string; content: string; cinematic?: Cinematic; sfx?: Sfx } }
    | { type: 'ADD_AI_ACTION_TO_LOG'; payload: { id: string, characterName: string; action: string; dialogue?: string } }
    | { type: 'ADD_SYSTEM_MESSAGE_TO_LOG'; payload: { id: string; content: string; diceRoll?: DiceRoll } }
    | { type: 'UPDATE_LAST_PLAYER_MESSAGE_INTERPRETATION'; payload: string }
    | { type: 'UPDATE_CINEMATIC_STATUS'; payload: { messageId: string; status: Cinematic['status']; assetKey?: string; url?: string; } }
    | { type: 'UPDATE_SFX_STATUS'; payload: { messageId: string; status: Sfx['status']; assetKey?: string; url?: string; } }
    | { type: 'SET_GAME_LOG_SUMMARY'; payload: string };

// Actions handled by miscReducer
export type MiscAction =
    | { type: 'SET_GAME_PHASE'; payload: GamePhase }
    | { type: 'UPDATE_ASSET_CACHE'; payload: { key: string; url: string } }
    | { type: 'ADD_VEHICLE'; payload: Vehicle }
    | { type: 'REMOVE_VEHICLE'; payload: { id: string } }
    | { type: 'ADD_REAL_ESTATE'; payload: RealEstate }
    | { type: 'REMOVE_REAL_ESTATE'; payload: { id: string } }
    | { type: 'ADD_KNOWN_LOCATION'; payload: { id: string; name: string; description: string } }
    | { type: 'SET_LOCATION'; payload: string }
    | { type: 'SET_GAME_MODE'; payload: GameState['gameMode'] }
    | { type: 'SET_ACTIVE_ENEMIES'; payload: GameState['activeEnemies'] }
    | { type: 'SET_RESOURCES'; payload: Record<string, number> }
    | { type: 'SET_FALLBACK_STATUS'; payload: boolean }
    | { type: 'RESTART_GAME' };

// Actions handled directly in rootReducer
export type RootReducerAction =
    | { type: 'START_GAME'; payload: { gameState: GameState } }
    | { type: 'POPULATE_GENERATED_DATA', payload: { gameState: GameState } }
    | { type: 'RESTORE_GAME_STATE'; payload: GameState }
    | { type: 'PROCESS_AI_RESPONSE'; payload: { result: PlayerActionSuccessResult; gmName: string; settings: { roundRobinInitiative: boolean; characterAgency: boolean; } } }
    | { type: 'UPDATE_COGNITIVE_STATE'; payload: Partial<CognitiveState> }
    | { type: 'SET_SUGGESTED_ACTIONS', payload: string[] }
    | { type: 'ADD_CRAFTING_INGREDIENT', payload: Item }
    | { type: 'REMOVE_CRAFTING_INGREDIENT', payload: { itemId: string } }
    | { type: 'CLEAR_CRAFTING_INGREDIENTS' };

// Union of all possible game actions
export type CombinedTrpgGameAction =
    | CharactersAction
    | InventoryAction
    | MapAction
    | GameLogAction
    | MiscAction
    | RootReducerAction;