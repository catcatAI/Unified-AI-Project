import { Game } from '../models/game.model';

// FIX: Replaced `title`, `description`, and `effectDescription` with their `*Key` counterparts
// to match the `MajorGameEvent` type, and updated values to be translation keys.
export const MAJOR_EVENTS: Game.MajorGameEvent[] = [
    {
        id: 'STRUCT_FAIL_1',
        titleKey: 'majorEvents.STRUCT_FAIL_1.title',
        descriptionKey: 'majorEvents.STRUCT_FAIL_1.description',
        effectDescriptionKey: 'majorEvents.STRUCT_FAIL_1.effectDescription',
        condition: (core, resources) => core.M3_Precision.value < 0.4 && resources.M_Si.amount > 500,
        effect: {
            type: 'resource',
            payload: {
                resource: 'M_Si',
                percentage: -0.25
            }
        }
    },
    {
        id: 'POP_ILLNESS_1',
        titleKey: 'majorEvents.POP_ILLNESS_1.title',
        descriptionKey: 'majorEvents.POP_ILLNESS_1.description',
        effectDescriptionKey: 'majorEvents.POP_ILLNESS_1.effectDescription',
        condition: (core, resources) => resources.POP.amount > 100 && core.M6_Security.value < 0.5,
        effect: {
            type: 'population',
            payload: {
                percentage: -0.10
            }
        }
    },
    {
        id: 'AETHER_FLUX_1',
        titleKey: 'majorEvents.AETHER_FLUX_1.title',
        descriptionKey: 'majorEvents.AETHER_FLUX_1.description',
        effectDescriptionKey: 'majorEvents.AETHER_FLUX_1.effectDescription',
        condition: (core, resources) => resources.L_A.amount > 150,
        effect: {
            type: 'resource',
            payload: {
                resource: 'L_A',
                percentage: -0.50
            }
        }
    }
];
