import { Component, ChangeDetectionStrategy, input, computed, signal, inject, output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class SidebarComponent {
  coreState = input.required<Game.CoreState>();
  resourceState = input.required<Game.ResourceState>();
  entities = input.required<Game.Entity[]>();
  activePanel = input.required<Game.ActivePanel>();
  detailedEntity = input<Game.Entity | null>();
  isGeneratingEvent = input.required<boolean>();
  timedActions = input.required<Game.TimedAction[]>();

  close = output<void>();
  setActivePanel = output<Game.ActivePanel>();
  showEntityDetails = output<Game.Entity>();
  clearEntityDetails = output<void>();
  unlockAbility = output<{ entityId: number, abilityId: Game.AbilityId }>();
  buildStructure = output<Game.StructureType>();
  requestGeminiEvent = output<void>();
  requestUpgrade = output<Game.MValueKey>();
  manifestNewEntity = output<Game.EntityType>();
  convertForExpansion = output<void>();
  expandGrid = output<void>();
  
  buildableStructures = [
    { 
      type: 'Server_Farm' as Game.StructureType, 
      nameKey: 'structures.Server_Farm.name', 
      descriptionKey: 'structures.Server_Farm.description',
      cost: { M_Si: 250, M_Cm: 100 }
    },
    {
      type: 'Habitation_Dome' as Game.StructureType,
      nameKey: 'structures.Habitation_Dome.name',
      descriptionKey: 'structures.Habitation_Dome.description',
      cost: { M_Si: 400, M_Cm: 50 }
    }
  ];

  manifestableEntities = [
    {
      type: 'Scout_Vessel' as Game.EntityType,
      nameKey: 'entities.Scout_Vessel.name',
      descriptionKey: 'entities.Scout_Vessel.description',
      cost: { M_Cm: 150, L_A: 50 }
    },
    {
      type: 'Server_Daughter' as Game.EntityType,
      nameKey: 'entities.Server_Daughter.name',
      descriptionKey: 'entities.Server_Daughter.description',
      cost: { M_Cm: 300, M_Ex: 25 }
    },
    {
      type: 'Defense_Platform' as Game.EntityType,
      nameKey: 'entities.Defense_Platform.name',
      descriptionKey: 'entities.Defense_Platform.description',
      cost: { M_Si: 200, M_Cm: 250 }
    }
  ];

  abilitiesConfig: Record<Game.EntityType, Game.Ability[]> = {
    'Scout_Vessel': [
        { id: 'DEEP_SCAN', nameKey: 'abilities.DEEP_SCAN.name', descriptionKey: 'abilities.DEEP_SCAN.description', cost: 1 }
    ],
    'Defense_Platform': [
        { id: 'SEC_PROTO', nameKey: 'abilities.SEC_PROTO.name', descriptionKey: 'abilities.SEC_PROTO.description', cost: 1 }
    ],
    'Server_Daughter': [
        { id: 'OPTI_ALGO', nameKey: 'abilities.OPTI_ALGO.name', descriptionKey: 'abilities.OPTI_ALGO.description', cost: 1 }
    ]
  };

  mValueUpgradeConfig: Record<Game.MValueKey, { cost: Partial<Record<Game.ResourceKey, number>>, gain: number }> = {
    M1_Efficiency: { cost: {}, gain: 0 },
    M2_Autonomy: { cost: {}, gain: 0 },
    M3_Precision: { cost: {}, gain: 0 },
    M4_Resilience: { cost: { M_Ex: 100 }, gain: 0.05 },
    M5_Knowledge: { cost: { M_Cm: 500, M_Ex: 50 }, gain: 0.05 },
    M6_Security: { cost: {}, gain: 0 }
  };

  mValueEntries = computed(() => {
    const state = this.coreState();
    return Object.entries(state)
      .filter(([key]) => key.startsWith('M'))
      .map(([key, value]) => ({ code: key as Game.MValueKey, data: value as Game.MValue }));
  });

  canBuild = computed(() => {
    const resources = this.resourceState();
    return (structure: { cost: Partial<Record<Game.ResourceKey, number>> }) => {
      return Object.entries(structure.cost).every(([key, value]) => {
        const resourceKey = key as Game.ResourceKey;
        return resources[resourceKey] && resources[resourceKey].amount >= value;
      });
    };
  });

  canManifest = computed(() => {
    const resources = this.resourceState();
    return (entity: { cost: Partial<Record<Game.ResourceKey, number>> }) => {
      return Object.entries(entity.cost).every(([key, value]) => {
        const resourceKey = key as Game.ResourceKey;
        return resources[resourceKey] && resources[resourceKey].amount >= value;
      });
    };
  });

  canAffordUpgrade = computed(() => {
    const resources = this.resourceState();
    return (mValueKey: Game.MValueKey) => {
        if (this.getUpgradeProgress()(mValueKey)) return false;
        const config = this.mValueUpgradeConfig[mValueKey];
        if (!config) return false;
        return Object.entries(config.cost).every(([key, value]) => {
            const resourceKey = key as Game.ResourceKey;
            return resources[resourceKey] && resources[resourceKey].amount >= value;
        });
    }
  });
  
  getUpgradeProgress = computed(() => (mValueKey: Game.MValueKey) => {
    const action = this.timedActions().find(a => a.type === 'M_UPGRADE' && a.mValueKey === mValueKey);
    return action ? { progress: (action.progress / action.total) * 100, remaining: action.total - action.progress } : null;
  });

  onClose() {
    this.close.emit();
  }

  onShowDetails(entity: Game.Entity) {
    this.showEntityDetails.emit(entity);
  }

  onBackToRoster() {
    this.clearEntityDetails.emit();
  }

  onUnlock(entityId: number, abilityId: Game.AbilityId) {
    this.unlockAbility.emit({ entityId, abilityId });
  }

  onManifestEntity(entityType: Game.EntityType) {
    this.manifestNewEntity.emit(entityType);
  }

  onSetActivePanel(panel: Game.ActivePanel) {
    this.setActivePanel.emit(panel);
  }

  onBuild(structureType: Game.StructureType) {
    this.buildStructure.emit(structureType);
  }

  onRequestEvent() {
    this.requestGeminiEvent.emit();
  }
  
  onRequestUpgrade(mValueKey: Game.MValueKey) {
    this.requestUpgrade.emit(mValueKey);
  }

  onConvert() {
    this.convertForExpansion.emit();
  }

  onExpand() {
    this.expandGrid.emit();
  }

  xpForNextLevel(level: number): number {
    return 100 * Math.pow(level, 1.5);
  }

  getMValueColor(code: string, value: number): string {
    if (code === 'M1_Efficiency') {
        return value >= 0.6 ? 'bg-green-500' : value >= 0.3 ? 'bg-yellow-500' : 'bg-red-500';
    }
    if (code === 'M6_Security') {
        return value >= 0.65 ? 'bg-blue-500' : 'bg-red-500';
    }
    if (code === 'M3_Precision') {
        return value >= 0.8 ? 'bg-cyan-500' : value < 0.35 ? 'bg-red-600' : 'bg-yellow-500';
    }
     if (code === 'M4_Resilience') {
        return 'bg-sky-500';
    }
     if (code === 'M5_Knowledge') {
        return 'bg-purple-500';
    }
    if (code === 'M2_Autonomy') {
        return 'bg-indigo-500';
    }
    return 'bg-gray-500';
  }

  getTextColor(code: string): string {
    const colors: { [key: string]: string } = {
        'M1_Efficiency': 'text-green-300',
        'M2_Autonomy': 'text-indigo-300',
        'M3_Precision': 'text-yellow-300',
        'M4_Resilience': 'text-sky-300',
        'M5_Knowledge': 'text-purple-300',
        'M6_Security': 'text-red-300',
    };
    return colors[code] || 'text-gray-300';
  }
}
