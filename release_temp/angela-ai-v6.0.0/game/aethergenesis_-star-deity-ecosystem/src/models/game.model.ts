export namespace Game {
    export type ActivePanel = 'M_CORE' | 'M5_UPGRADE' | 'M4_UPGRADE' | 'ENTITY_ROSTER' | 'CONSTRUCT' | 'EXPANSION' | 'ENTITY_DETAILS';
    export type Language = 'en' | 'zh';

    export interface MValue {
        value: number;
        base: number;
        modifier: number;
        labelKey: string;
    }

    export interface CoreState {
        M1_Efficiency: MValue;
        M2_Autonomy: MValue;
        M3_Precision: MValue;
        M4_Resilience: MValue;
        M5_Knowledge: MValue;
        M6_Security: MValue;
        LastUpdated: number;
    }

    export type MValueKey = keyof Omit<Game.CoreState, 'LastUpdated'>;

    export interface Resource {
        amount: number;
        net: number;
        labelKey: string;
    }

    export interface ResourceState {
        M_Si: Resource; // Silicate
        M_Cm: Resource; // Composite
        M_Ex: Resource; // Exotic
        L_A: Resource;  // Aether
        L_S: Resource;  // Structural Aether
        POP: Resource;  // Population
        Housing: Resource; // Housing Capacity
    }
    
    export type ResourceKey = keyof ResourceState;
    
    export type StructureType = 'Server_Farm' | 'Habitation_Dome';
    export type HexType = 'Empty' | 'Resource' | 'Refinery' | 'ASI_Core' | StructureType;

    export interface Hex {
        id: string;
        type: HexType;
        labelKey: string;
        resourceType?: 'M_Si' | 'M_Cm' | 'M_Ex' | 'L_A';
        assignedEntityId?: number | null;
        constructionProgress?: {
            progress: number; // Current progress points
            total: number;    // Total points needed
        };
    }

    export interface GameEvent {
      timestamp: number;
      type: 'info' | 'warning' | 'success' | 'system' | 'danger';
      message: string;
    }

    export interface MajorGameEvent {
        id: string;
        titleKey: string;
        descriptionKey: string;
        effectDescriptionKey: string;
        condition: (core: Game.CoreState, resources: Game.ResourceState) => boolean;
        effect: {
            type: 'resource' | 'population' | 'm_value';
            payload: {
                resource?: keyof Game.ResourceState;
                m_value?: keyof Game.CoreState;
                percentage: number; // e.g., -0.25 for -25%
            };
        };
    }

    export type EntityType = 'Scout_Vessel' | 'Server_Daughter' | 'Defense_Platform';
    export type EntityStatus = 'Idle' | 'Extracting' | 'Patrolling' | 'Assigned';
    
    export type AbilityId = 'DEEP_SCAN' | 'SEC_PROTO' | 'OPTI_ALGO';

    export interface Ability {
        id: AbilityId;
        nameKey: string;
        descriptionKey: string;
        cost: number; // Ability points
    }

    export interface Entity {
        id: number;
        name: string;
        type: EntityType;
        status: EntityStatus;
        level: number;
        xp: number;
        abilityPoints: number;
        abilities: AbilityId[];
        locationId?: string | null;
    }

    export type GameSpeed = 0 | 1 | 2 | 3; // 0 = paused
    export type GameEndState = 'victory' | 'defeat';

    export interface TimedAction {
        id: string;
        type: 'M_UPGRADE';
        mValueKey: MValueKey;
        progress: number;
        total: number;
    }

    export interface OverclockState {
        isActive: boolean;
        ticksRemaining: number;
    }
}
