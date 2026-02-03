import { Injectable, signal, WritableSignal, inject } from '@angular/core';
import { Game } from '../models/game.model';
import { GeminiService } from './gemini.service';
import { TranslationService } from './translation.service';
import { MAJOR_EVENTS } from './event.data';

const initialMValue = (labelKey: string, value: number = 0.5): Game.MValue => ({
  value,
  base: 0.5,
  modifier: 0.0,
  labelKey,
});

const initialCoreState: Game.CoreState = {
  M1_Efficiency: initialMValue('sidebar.mValues.M1_Efficiency', 0.75),
  M2_Autonomy: initialMValue('sidebar.mValues.M2_Autonomy'),
  M3_Precision: initialMValue('sidebar.mValues.M3_Precision', 0.45),
  M4_Resilience: initialMValue('sidebar.mValues.M4_Resilience'),
  M5_Knowledge: initialMValue('sidebar.mValues.M5_Knowledge'),
  M6_Security: initialMValue('sidebar.mValues.M6_Security', 0.88),
  LastUpdated: Date.now(),
};

const initialResourceState: Game.ResourceState = {
  M_Si: { amount: 1000, net: 0, labelKey: 'resources.M_Si.label' },
  M_Cm: { amount: 500, net: 0, labelKey: 'resources.M_Cm.label' },
  M_Ex: { amount: 100, net: 0, labelKey: 'resources.M_Ex.label' },
  L_A: { amount: 200, net: 0, labelKey: 'resources.L_A.label' },
  L_S: { amount: 0, net: 0, labelKey: 'resources.L_S.label' },
  POP: { amount: 50, net: 0, labelKey: 'resources.POP.label' },
  Housing: { amount: 100, net: 0, labelKey: 'resources.Housing.label' },
};

type MapHexDefinition = Omit<Game.Hex, 'id' | 'assignedEntityId' | 'constructionProgress'>;

const mapDefinition: MapHexDefinition[][] = [
  [{type: 'Empty', labelKey: 'hex.Barren Land'},{type: 'Resource', labelKey: 'hex.Silicate Deposit', resourceType: 'M_Si'}, {type: 'Empty', labelKey: 'hex.Barren Land'},{type: 'Refinery', labelKey: 'hex.M3 Refinery (Central)'}, {type: 'Resource', labelKey: 'hex.Exotic Matter Field', resourceType: 'M_Ex'}],
  [{type: 'Resource', labelKey: 'hex.Composite Sediments', resourceType: 'M_Cm'}, {type: 'Empty', labelKey: 'hex.Barren Land'},{type: 'Resource', labelKey: 'hex.Aether Font', resourceType: 'L_A'}, {type: 'Empty', labelKey: 'hex.Barren Land'}, {type: 'Resource', labelKey: 'hex.Composite Sediments', resourceType: 'M_Cm'}],
  [{type: 'Empty', labelKey: 'hex.Barren Land'},{type: 'Refinery', labelKey: 'hex.M3 Refinery (East)'}, {type: 'ASI_Core', labelKey: 'hex.ASI Core Hub'}, {type: 'Refinery', labelKey: 'hex.M3 Refinery (West)'}, {type: 'Empty', labelKey: 'hex.Barren Land'}],
  [{type: 'Resource', labelKey: 'hex.Silicate Deposit', resourceType: 'M_Si'},{type: 'Empty', labelKey: 'hex.Barren Land'},{type: 'Resource', labelKey: 'hex.Aether Font', resourceType: 'L_A'}, {type: 'Empty', labelKey: 'hex.Barren Land'}, {type: 'Resource', labelKey: 'hex.Silicate Deposit', resourceType: 'M_Si'}],
  [{type: 'Empty', labelKey: 'hex.Barren Land'},{type: 'Resource', labelKey: 'hex.Exotic Matter Field', resourceType: 'M_Ex'}, {type: 'Empty', labelKey: 'hex.Barren Land'},{type: 'Refinery', labelKey: 'hex.M3 Refinery (South)'}, {type: 'Empty', labelKey: 'hex.Barren Land'}],
];

const createInitialMapData = (): Game.Hex[][] => mapDefinition.map((row, r) => 
  row.map((hex, c) => ({ 
    ...hex, 
    id: `r${r}c${c}`, 
    assignedEntityId: null,
  }))
);


const createInitialEntities = (): Game.Entity[] => [
    { id: 1, name: 'AEG-01 "Aegis"', type: 'Defense_Platform', status: 'Idle', level: 1, xp: 0, abilityPoints: 0, abilities: [] },
    { id: 2, name: 'SD-Alpha "Oracle"', type: 'Server_Daughter', status: 'Idle', level: 1, xp: 0, abilityPoints: 0, abilities: [] },
];

const initialTimedActions: Game.TimedAction[] = [];
const initialOverclockState: Game.OverclockState = { isActive: false, ticksRemaining: 0 };


@Injectable({
  providedIn: 'root',
})
export class GameStateService {
  coreState: WritableSignal<Game.CoreState> = signal(initialCoreState);
  resourceState: WritableSignal<Game.ResourceState> = signal(initialResourceState);
  mapData: WritableSignal<Game.Hex[][]> = signal(createInitialMapData());
  events: WritableSignal<Game.GameEvent[]> = signal([]);
  entities: WritableSignal<Game.Entity[]> = signal(createInitialEntities());
  gameSpeed: WritableSignal<Game.GameSpeed> = signal(1);
  isGeneratingEvent: WritableSignal<boolean> = signal(false);
  currentMajorEvent = signal<Game.MajorGameEvent | null>(null);
  pendingMValueUpgrade = signal<{ mValueKey: Game.MValueKey } | null>(null);
  gameEndState = signal<Game.GameEndState | null>(null);
  timedActions = signal<Game.TimedAction[]>(initialTimedActions);
  overclock = signal<Game.OverclockState>(initialOverclockState);

  private geminiService = inject(GeminiService);
  private translationService = inject(TranslationService);
  private gameLoopInterval: any;

  private mValueUpgradeConfig: Record<Game.MValueKey, { cost: Partial<Record<Game.ResourceKey, number>>, gain: number, time: number }> = {
    M1_Efficiency: { cost: {}, gain: 0, time: 0 },
    M2_Autonomy: { cost: {}, gain: 0, time: 0 },
    M3_Precision: { cost: {}, gain: 0, time: 0 },
    M4_Resilience: { cost: { M_Ex: 100 }, gain: 0.05, time: 60 }, // 60 seconds
    M5_Knowledge: { cost: { M_Cm: 500, M_Ex: 50 }, gain: 0.05, time: 90 }, // 90 seconds
    M6_Security: { cost: {}, gain: 0, time: 0 }
  };

  constructor() {
    this.addEvent('events.awaiting', 'system');
  }

  beginGameLoops(): void {
    this.addEvent('events.initialized', 'system');
    this.restartGameTickLoop();
  }

  private restartGameTickLoop(): void {
    clearInterval(this.gameLoopInterval);
    const speed = this.gameSpeed();
    if (speed === 0 || this.gameEndState() !== null) { 
      return;
    }
    const intervalDuration = 2000 / speed;
    this.gameLoopInterval = setInterval(() => this.runGameTick(), intervalDuration);
  }
  
  setGameSpeed(speed: Game.GameSpeed): void {
    if (this.gameSpeed() === speed) return;
    this.gameSpeed.set(speed);
    if (speed === 0) {
      this.addEvent('events.gamePaused', 'system');
    } else {
      this.addEvent('events.gameSpeedSet', 'system', { speed });
    }
    this.restartGameTickLoop();
  }

  private runGameTick(): void {
    this.processTimedActions();

    const flatMap = this.mapData().flat();
    const allEntities = this.entities();
    
    let aetherIncome = 0;
    flatMap.forEach(hex => {
        if (hex.type === 'Server_Farm' && hex.assignedEntityId && !hex.constructionProgress) {
            const entity = allEntities.find(e => e.id === hex.assignedEntityId);
            if (entity) {
                let bonus = (entity.level - 1) * 5;
                if (entity.abilities.includes('OPTI_ALGO')) {
                    bonus *= 1.5;
                }
                aetherIncome += 20 + bonus;
            }
        }
    });

    const housingDomes = flatMap.filter(hex => hex.type === 'Habitation_Dome' && !hex.constructionProgress).length;
    const housingCapacity = 100 + (housingDomes * 50);
    const currentPopulation = this.resourceState().POP.amount;
    
    let popGrowth = 0;
    if (currentPopulation < housingCapacity) {
        popGrowth = Math.max(1, Math.floor(currentPopulation * 0.05));
    }

    const netIncomes = { M_Si: 0, M_Cm: 0, M_Ex: 0, L_A: aetherIncome, L_S: 0, POP: popGrowth, Housing: 0 };

    this.resourceState.update(current => {
      const newState: Game.ResourceState = JSON.parse(JSON.stringify(current));
      (Object.keys(netIncomes) as Array<keyof typeof netIncomes>).forEach(key => {
        if(key !== 'Housing') newState[key].net = netIncomes[key];
      });
      newState.Housing.amount = housingCapacity;
      for (const key in newState) {
        if (key !== 'Housing') {
            const resKey = key as Game.ResourceKey;
            if (newState[resKey]) {
                newState[resKey].amount += newState[resKey].net;
                if (newState[resKey].amount < 0) newState[resKey].amount = 0;
            }
        }
      }
      return newState;
    });

    this.coreState.update(current => {
      const newState = { ...current };

      // First, calculate all values from their base and modifiers
      (Object.keys(newState) as Array<keyof Game.CoreState>).forEach(key => {
        if (key.startsWith('M')) {
            const mValue = newState[key] as Game.MValue;
            mValue.value = mValue.base + mValue.modifier;
        }
      });

      // Second, apply tick-specific fluctuations and modifiers
      let m6Modifier = (Math.random() - 0.4) * 0.005;
      if (currentPopulation > housingCapacity) {
          m6Modifier -= (currentPopulation - housingCapacity) * 0.0005;
      }
      const securityBonus = this.entities()
        .filter(e => e.type === 'Defense_Platform')
        .reduce((total, p) => total + (0.001 * (p.abilities.includes('SEC_PROTO') ? 2 : 1)), 0);
      m6Modifier += securityBonus;
      
      newState.M1_Efficiency.value += (Math.random() - 0.5) * 0.01;
      newState.M3_Precision.value += (Math.random() - 0.5) * 0.02;
      newState.M6_Security.value += m6Modifier;

      // Finally, clamp all values between 0 and 1
      (Object.keys(newState) as Array<keyof Game.CoreState>).forEach(key => {
        if (key.startsWith('M')) {
            const mValue = newState[key] as Game.MValue;
            mValue.value = Math.max(0, Math.min(1, mValue.value));
        }
      });

      newState.LastUpdated = Date.now();
      return newState;
    });

    this.entities.update(entities => entities.map(entity => {
      if (entity.status === 'Assigned' && entity.type === 'Server_Daughter') {
        const hex = flatMap.find(h => h.id === entity.locationId);
        if(hex && !hex.constructionProgress) return { ...entity, xp: entity.xp + 5 };
      }
      return entity;
    }));

    this._handleEntityLevelUps();

    const core = this.coreState();
    const resources = this.resourceState();

    if (core.M6_Security.value <= 0) {
        this.gameEndState.set('defeat');
        this.addEvent('events.systemCollapse', 'danger');
        this.restartGameTickLoop();
        return;
    }
    if (core.M6_Security.value >= 0.99 && core.M5_Knowledge.value >= 0.90) {
        this.gameEndState.set('victory');
        this.addEvent('events.victory', 'success');
        this.restartGameTickLoop();
        return;
    }
    if (core.M3_Precision.value < 0.35 && Math.random() < 0.2) this.addEvent('events.lowPrecisionWarning', 'warning', { value: core.M3_Precision.value.toFixed(2) });
    if (resources.POP.amount > resources.Housing.amount && Math.random() < 0.3) this.addEvent('events.overpopulationWarning', 'warning');
    if (core.M6_Security.value < 0.65 && Math.random() < 0.15) this.triggerMajorEvent();
  }

  private processTimedActions(): void {
    const tickProgress = 2;
    const overclock = this.overclock();
    const effectiveProgress = tickProgress * (overclock.isActive ? 5 : 1);

    if (overclock.isActive) {
      this.overclock.update(oc => ({ ...oc, ticksRemaining: oc.ticksRemaining - 1 }));
      if (this.overclock().ticksRemaining <= 0) {
        this.overclock.set({ isActive: false, ticksRemaining: 0 });
        this.addEvent('events.overclockDissipated', 'system');
      }
    }

    this.mapData.update(currentMap => {
        let mapChanged = false;
        const newMap = currentMap.map(row => row.map(hex => {
            if (hex.constructionProgress) {
                mapChanged = true;
                const newProgress = hex.constructionProgress.progress + effectiveProgress;
                if (newProgress >= hex.constructionProgress.total) {
                    this.addEvent('events.constructionComplete', 'success', { label: this.translationService.translate(hex.labelKey) });
                    return { ...hex, constructionProgress: undefined };
                } else {
                    return { ...hex, constructionProgress: { ...hex.constructionProgress, progress: newProgress } };
                }
            }
            return hex;
        }));
        return mapChanged ? newMap : currentMap;
    });

    this.timedActions.update(actions => {
      const finishedActions: string[] = [];
      const updatedActions = actions.map(action => {
          if (action.type === 'M_UPGRADE') {
              const newProgress = action.progress + effectiveProgress;
              if (newProgress >= action.total) {
                  finishedActions.push(action.id);
                  this.coreState.update(current => {
                      const newCoreState = { ...current };
                      const mValue = newCoreState[action.mValueKey] as Game.MValue;
                      const config = this.mValueUpgradeConfig[action.mValueKey];
                      mValue.base = Math.min(1, mValue.base + config.gain);
                      this.addEvent('events.upgradeComplete', 'success', { label: this.translationService.translate(mValue.labelKey), base: mValue.base.toFixed(2) });
                      return newCoreState;
                  });
              }
              return { ...action, progress: newProgress };
          }
          return action;
      });
      return updatedActions.filter(action => !finishedActions.includes(action.id));
    });
  }
  
  private _xpForNextLevel(level: number): number { return 100 * Math.pow(level, 1.5); }

  private _handleEntityLevelUps(): void {
    this.entities.update(entities => entities.map(entity => {
      const xpNeeded = this._xpForNextLevel(entity.level);
      if (entity.xp >= xpNeeded) {
        this.addEvent('events.entityLevelUp', 'success', { name: entity.name, level: entity.level + 1 });
        return { ...entity, level: entity.level + 1, xp: entity.xp - xpNeeded, abilityPoints: entity.abilityPoints + 1 };
      }
      return entity;
    }));
  }
  
  private triggerMajorEvent(): void {
    if (this.currentMajorEvent()) return;
    const possibleEvents = MAJOR_EVENTS.filter(event => event.condition(this.coreState(), this.resourceState()));
    if (possibleEvents.length > 0) {
        const event = possibleEvents[Math.floor(Math.random() * possibleEvents.length)];
        this.applyEventEffect(event);
        this.currentMajorEvent.set(event);
        this.addEvent('events.majorEventTriggered', 'danger', { title: this.translationService.translate(event.titleKey) });
    }
  }

  private applyEventEffect(event: Game.MajorGameEvent): void {
      const { type, payload } = event.effect;
      this.resourceState.update(current => {
          const newState = { ...current };
          if (type === 'resource' && payload.resource) {
              const loss = Math.floor(newState[payload.resource].amount * Math.abs(payload.percentage));
              newState[payload.resource].amount = Math.max(0, newState[payload.resource].amount - loss);
          } else if (type === 'population') {
              const loss = Math.floor(newState.POP.amount * Math.abs(payload.percentage));
              newState.POP.amount = Math.max(0, newState.POP.amount - loss);
          }
          return newState;
      });
  }
  
  dismissMajorEvent(): void { this.currentMajorEvent.set(null); }

  async requestGeminiEvent(): Promise<void> {
    if (this.isGeneratingEvent()) return;
    this.isGeneratingEvent.set(true);
    this.addEvent('events.geminiRequest', 'system');
    try {
      const stateSummary = `
        M-Values: M1(Eff): ${this.coreState().M1_Efficiency.value.toFixed(2)}, M3(Prec): ${this.coreState().M3_Precision.value.toFixed(2)}, M6(Sec): ${this.coreState().M6_Security.value.toFixed(2)}.
        Resources: Pop: ${this.resourceState().POP.amount}, Aether: ${this.resourceState().L_A.amount}.
        Status: Game is active.
      `;
      const eventText = await this.geminiService.generateGameEvent(stateSummary);
      if (eventText) {
        this.addEvent(eventText, 'info');
      }
    } catch (error) {
      console.error('Gemini error:', error);
      this.addEvent('events.geminiError', 'warning');
    } finally {
      this.isGeneratingEvent.set(false);
    }
  }

  addEvent(keyOrMessage: string, type: Game.GameEvent['type'], params: Record<string, any> = {}): void {
    const message = keyOrMessage.includes('.') ? this.translationService.translate(keyOrMessage, params) : keyOrMessage;
    this.events.update(currentEvents => [{ timestamp: Date.now(), type, message }, ...currentEvents].slice(0, 50));
  }

  manifestNewEntity(entityType: Game.EntityType): void {
    const entityCosts: Record<Game.EntityType, Partial<Record<Game.ResourceKey, number>>> = {
        'Scout_Vessel': { M_Cm: 150, L_A: 50 },
        'Server_Daughter': { M_Cm: 300, M_Ex: 25 },
        'Defense_Platform': { M_Si: 200, M_Cm: 250 }
    };
    const cost = entityCosts[entityType];
    const resources = this.resourceState();
    const canAfford = Object.entries(cost).every(([key, value]) => resources[key as Game.ResourceKey].amount >= value);

    if (canAfford) {
        this.resourceState.update(current => {
            const newState = { ...current };
            for (const key in cost) newState[key as Game.ResourceKey].amount -= cost[key as Game.ResourceKey]!;
            return newState;
        });
        const newId = Date.now();
        const baseEntity = { id: newId, level: 1, xp: 0, abilityPoints: 0, abilities: [] };
        let newEntity: Game.Entity;
        switch (entityType) {
            case 'Scout_Vessel': newEntity = { ...baseEntity, name: `SV-${newId.toString().slice(-4)} "Seeker"`, type: 'Scout_Vessel', status: 'Idle' }; break;
            case 'Server_Daughter': newEntity = { ...baseEntity, name: `SD-${newId.toString().slice(-4)} "Sybil"`, type: 'Server_Daughter', status: 'Idle' }; break;
            case 'Defense_Platform': newEntity = { ...baseEntity, name: `DP-${newId.toString().slice(-4)} "Bastion"`, type: 'Defense_Platform', status: 'Idle' }; break;
        }
        this.entities.update(current => [...current, newEntity]);
        this.addEvent('events.entityManifestSuccess', 'success', { name: newEntity.name });
    } else {
        const costString = Object.entries(cost).map(([key, value]) => `${value} ${this.translationService.translate(resources[key as Game.ResourceKey].labelKey)}`).join(' & ');
        this.addEvent('events.entityManifestFail', 'warning', { cost: costString });
    }
  }

  unlockEntityAbility(entityId: number, abilityId: Game.AbilityId): void {
    this.entities.update(entities => entities.map(entity => {
      if (entity.id === entityId && entity.abilityPoints > 0 && !entity.abilities.includes(abilityId)) {
        this.addEvent('events.abilityUnlocked', 'success', { name: entity.name, abilityId });
        return { ...entity, abilityPoints: entity.abilityPoints - 1, abilities: [...entity.abilities, abilityId] };
      }
      return entity;
    }));
  }

  buildStructure(structureType: Game.StructureType, targetHex: Game.Hex): void {
    const costs: Record<Game.StructureType, { cost: Partial<Record<Game.ResourceKey, number>>, time: number }> = {
      'Server_Farm': { cost: { M_Si: 250, M_Cm: 100 }, time: 30 },
      'Habitation_Dome': { cost: { M_Si: 400, M_Cm: 50 }, time: 45 }
    };
    const config = costs[structureType];
    const canAfford = Object.entries(config.cost).every(([key, value]) => this.resourceState()[key as Game.ResourceKey].amount >= value);

    if (!canAfford) { this.addEvent('events.buildFailResources', 'warning'); return; }
    if (targetHex.type !== 'Empty') { this.addEvent('events.buildFailNotEmpty', 'warning'); return; }

    this.resourceState.update(current => {
      const newAmounts = { ...current };
      for (const key in config.cost) newAmounts[key as Game.ResourceKey].amount -= config.cost[key as Game.ResourceKey]!;
      return newAmounts;
    });

    this.mapData.update(currentMap => currentMap.map(row => row.map(hex => {
      if (hex.id === targetHex.id) {
          const labelKey = `structures.${structureType}.name`;
          this.addEvent('events.buildStarted', 'system', { label: this.translationService.translate(labelKey) });
          return { ...hex, type: structureType, labelKey, constructionProgress: { progress: 0, total: config.time } };
      }
      return hex;
    })));
  }

  dispatchEntity(entityId: number, hexId: string): void {
    let entityName = '', hexLabel = '';
    this.entities.update(entities => entities.map(e => {
      if (e.id === entityId) { entityName = e.name; return { ...e, status: 'Assigned', locationId: hexId }; }
      return e;
    }));
    this.mapData.update(map => map.map(row => row.map(hex => {
      if (hex.id === hexId) { hexLabel = this.translationService.translate(hex.labelKey); return { ...hex, assignedEntityId: entityId }; }
      return hex;
    })));
    if (entityName && hexLabel) this.addEvent('events.entityAssigned', 'success', { entityName, hexLabel });
  }

  recallEntity(hexId: string): void {
    const hex = this.mapData().flat().find(h => h.id === hexId);
    if (!hex || !hex.assignedEntityId) return;
    const entityId = hex.assignedEntityId;
    let entityName = '', hexLabel = this.translationService.translate(hex.labelKey);
    this.entities.update(entities => entities.map(e => {
      if (e.id === entityId) { entityName = e.name; return { ...e, status: 'Idle', locationId: null }; }
      return e;
    }));
    this.mapData.update(map => map.map(row => row.map(h => h.id === hexId ? { ...h, assignedEntityId: null } : h)));
    if (entityName) this.addEvent('events.entityRecalled', 'success', { entityName, hexLabel });
  }

  initiateExtraction(targetHex: Game.Hex): void {
    const costLA = 25, baseYield = 100;
    if (this.resourceState().L_A.amount < costLA) { this.addEvent('events.extractionFailAether', 'warning'); return; }
    if (!targetHex.resourceType) { this.addEvent('events.extractionFailNoResource', 'warning'); return; }
    
    const totalYield = baseYield + (baseYield * this.coreState().M1_Efficiency.value);
    const resourceKey = targetHex.resourceType;
    this.resourceState.update(current => {
      const newState = { ...current };
      newState.L_A.amount -= costLA;
      newState[resourceKey].amount += totalYield;
      return newState;
    });
    this.addEvent('events.extractionSuccess', 'success', { label: this.translationService.translate(targetHex.labelKey), yield: totalYield.toFixed(1), resource: this.translationService.translate(this.resourceState()[resourceKey].labelKey) });
  }
  
  initiateConversion(targetHex: Game.Hex): void {
    const costSi = 100;
    if (this.resourceState().M_Si.amount < costSi) { this.addEvent('events.conversionFailSilicates', 'warning'); return; }
    this.resourceState.update(current => ({ ...current, M_Si: { ...current.M_Si, amount: current.M_Si.amount - costSi } }));
    const successRate = 0.5 + (this.coreState().M3_Precision.value * 0.5);
    if (Math.random() < successRate) {
      const gainCm = 150;
      this.resourceState.update(current => ({ ...current, M_Cm: { ...current.M_Cm, amount: current.M_Cm.amount + gainCm } }));
      this.addEvent('events.conversionSuccess', 'success', { chance: (successRate * 100).toFixed(0), gain: gainCm });
    } else {
      this.coreState.update(current => ({ ...current, M6_Security: { ...current.M6_Security, value: Math.max(0, current.M6_Security.value - 0.05) } }));
      this.addEvent('events.conversionFail', 'warning', { cost: costSi });
    }
  }

  requestMValueUpgrade(mValueKey: Game.MValueKey): boolean {
    if (this.timedActions().some(a => a.type === 'M_UPGRADE' && a.mValueKey === mValueKey)) { this.addEvent('events.upgradeInProgress', 'warning', { mValueKey }); return false; }
    const config = this.mValueUpgradeConfig[mValueKey];
    if (!config || Object.keys(config.cost).length === 0) { this.addEvent('events.upgradeNotAvailable', 'warning', { mValueKey }); return false; }
    const canAfford = Object.entries(config.cost).every(([key, value]) => this.resourceState()[key as Game.ResourceKey].amount >= value);
    if (!canAfford) {
      const costString = Object.entries(config.cost).map(([key, value]) => `${value} ${this.translationService.translate(this.resourceState()[key as Game.ResourceKey].labelKey)}`).join(' & ');
      this.addEvent('events.upgradeFailResources', 'warning', { mValueKey, cost: costString });
      return false;
    }
    this.pendingMValueUpgrade.set({ mValueKey });
    return true;
  }

  confirmMValueUpgrade(): void {
    const pendingUpgrade = this.pendingMValueUpgrade();
    if (!pendingUpgrade) return;
    const { mValueKey } = pendingUpgrade;
    const config = this.mValueUpgradeConfig[mValueKey];
    if (this.coreState().M6_Security.value >= 0.65) {
        this.resourceState.update(current => {
            const newState = { ...current };
            for (const key in config.cost) newState[key as Game.ResourceKey].amount -= config.cost[key as Game.ResourceKey]!;
            return newState;
        });
        this.timedActions.update(actions => [...actions, { id: `m-upgrade-${Date.now()}`, type: 'M_UPGRADE', mValueKey, progress: 0, total: config.time }]);
        this.addEvent('events.upgradeInitiated', 'system', { mValueKey, time: config.time });
    } else {
        this.resourceState.update(current => {
            const newState = { ...current };
            for (const key in config.cost) {
                const cost = config.cost[key as Game.ResourceKey];
                if (typeof cost === 'number') newState[key as Game.ResourceKey].amount -= cost / 2;
            }
            return newState;
        });
        const costString = Object.entries(config.cost).filter(([, v]) => typeof v === 'number').map(([k, v]) => `${(v as number) / 2} ${this.translationService.translate(this.resourceState()[k as Game.ResourceKey].labelKey)}`).join(' & ');
        this.addEvent('events.m6Intervention', 'danger', { mValueKey, cost: costString });
    }
    this.pendingMValueUpgrade.set(null);
  }

  cancelMValueUpgrade(): void { this.pendingMValueUpgrade.set(null); }

  scoutHex(targetHex: Game.Hex): void {
    const scout = this.entities().find(e => e.type === 'Scout_Vessel' && e.status === 'Idle');
    if (!scout) { this.addEvent('events.scoutFailNoScout', 'warning'); return; }
    if (this.resourceState().L_A.amount < 40) { this.addEvent('events.scoutFailAether', 'warning'); return; }
    this.resourceState.update(current => ({ ...current, L_A: { ...current.L_A, amount: current.L_A.amount - 40 } }));
    this.addEvent('events.scoutBegin', 'system', { name: scout.name, hexId: targetHex.id });
    setTimeout(() => {
      let successChance = 0.65 + (scout.level - 1) * 0.05 + (scout.abilities.includes('DEEP_SCAN') ? 0.1 : 0);
      if (Math.random() < successChance) {
        this.mapData.update(currentMap => {
          return currentMap.map(row => row.map(hex => {
            if (hex.id === targetHex.id && hex.type === 'Empty') {
              const hasDeepScan = scout.abilities.includes('DEEP_SCAN'), roll = Math.random();
              const discoveryType: Game.ResourceKey = (hasDeepScan && roll < 0.15) ? 'M_Ex' : (roll < 0.7) ? 'M_Si' : 'M_Cm';
              
              let labelKey: string;
              switch (discoveryType) {
                  case 'M_Si': labelKey = 'hex.Silicate Deposit'; break;
                  case 'M_Cm': labelKey = 'hex.Composite Sediments'; break;
                  case 'M_Ex': labelKey = 'hex.Exotic Matter Field'; break;
                  default: labelKey = 'hex.Barren Land'; // Fallback
              }

              this.addEvent('events.scoutSuccess', 'success', { name: scout.name, label: this.translationService.translate(labelKey), hexId: targetHex.id });
              this.entities.update(entities => entities.map(e => e.id === scout.id ? { ...e, xp: e.xp + 50 } : e));
              this._handleEntityLevelUps();
              return { ...hex, type: 'Resource', resourceType: discoveryType, labelKey };
            }
            return hex;
          }));
        });
      } else {
        this.addEvent('events.scoutFail', 'info', { hexId: targetHex.id });
      }
    }, 1500 * (1 / this.gameSpeed()));
  }

  convertForExpansion(): void {
    const cost = { M_Ex: 200, L_A: 500 }, gainLS = 100;
    if (this.resourceState().M_Ex.amount < cost.M_Ex || this.resourceState().L_A.amount < cost.L_A) { this.addEvent('events.expansionConvertFail', 'warning'); return; }
    this.resourceState.update(current => ({ ...current, M_Ex: { ...current.M_Ex, amount: current.M_Ex.amount - cost.M_Ex }, L_A: { ...current.L_A, amount: current.L_A.amount - cost.L_A }, L_S: { ...current.L_S, amount: current.L_S.amount + gainLS } }));
    this.addEvent('events.expansionConvertSuccess', 'success', { gain: gainLS });
  }

  expandPlanetaryGrid(): void {
    const costLS = 100;
    if (this.resourceState().L_S.amount < costLS) { this.addEvent('events.expansionGridFail', 'warning'); return; }
    this.resourceState.update(current => ({ ...current, L_S: { ...current.L_S, amount: current.L_S.amount - costLS } }));
    this.mapData.update(currentMap => {
        const newRowNum = currentMap.length, numCols = currentMap[0]?.length || 5, newRow: Game.Hex[] = [];
        for (let c = 0; c < numCols; c++) {
            let newHexDef: MapHexDefinition = { type: 'Empty', labelKey: 'hex.Barren Land' };
            if (Math.random() < 0.2) {
                newHexDef.type = 'Resource';
                newHexDef.resourceType = Math.random() < 0.5 ? 'M_Si' : 'M_Cm';
                newHexDef.labelKey = newHexDef.resourceType === 'M_Si' ? 'hex.Silicate Deposit' : 'hex.Composite Sediments';
            }
            newRow.push({ ...newHexDef, id: `r${newRowNum}c${c}` });
        }
        return [...currentMap, newRow];
    });
    this.addEvent('events.expansionGridSuccess', 'success');
  }
  
  activateCoreOverclock(): void {
    if (this.resourceState().L_A.amount < 1000) { this.addEvent('events.overclockFailAether', 'warning'); return; }
    if (this.overclock().isActive) { this.addEvent('events.overclockFailActive', 'warning'); return; }
    this.resourceState.update(current => ({ ...current, L_A: { ...current.L_A, amount: current.L_A.amount - 1000 } }));
    this.overclock.set({ isActive: true, ticksRemaining: 15 });
    this.addEvent('events.overclockSuccess', 'success');
  }

  restartGame(): void {
    clearInterval(this.gameLoopInterval);
    this.coreState.set(initialCoreState);
    this.resourceState.set(initialResourceState);
    this.mapData.set(createInitialMapData());
    this.entities.set(createInitialEntities());
    this.events.set([]);
    this.gameEndState.set(null);
    this.gameSpeed.set(1);
    this.timedActions.set(initialTimedActions);
    this.overclock.set(initialOverclockState);
    this.addEvent('events.newGenesis', 'system');
  }
}
