import { Component, ChangeDetectionStrategy, input, output, EventEmitter, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-action-panel',
  templateUrl: './action-panel.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class ActionPanelComponent {
  selectedHex = input<Game.Hex | null>();
  coreState = input.required<Game.CoreState>();
  resourceState = input.required<Game.ResourceState>();
  entities = input.required<Game.Entity[]>();
  overclock = input.required<Game.OverclockState>();
  
  setActivePanel = output<Game.ActivePanel>();
  dispatchEntity = output<{ entityId: number, hexId: string }>();
  recallEntity = output<string>();
  initiateExtraction = output<Game.Hex>();
  initiateConversion = output<Game.Hex>();
  scoutHex = output<Game.Hex>();
  activateCoreOverclock = output<void>();

  availableServerDaughter = computed(() => {
    return this.entities().find(e => e.type === 'Server_Daughter' && e.status === 'Idle');
  });

  availableScoutVessel = computed(() => {
    return this.entities().find(e => e.type === 'Scout_Vessel' && e.status === 'Idle');
  });

  assignedEntity = computed(() => {
    const hex = this.selectedHex();
    if (!hex || !hex.assignedEntityId) {
      return null;
    }
    return this.entities().find(e => e.id === hex.assignedEntityId);
  });

  serverDaughterBonus = computed(() => {
    const entity = this.assignedEntity();
    if (entity && entity.type === 'Server_Daughter') {
      let bonus = (entity.level - 1) * 5;
      if (entity.abilities.includes('OPTI_ALGO')) {
          bonus *= 1.5;
      }
      return bonus;
    }
    return 0;
  });

  scoutSuccessChance = computed(() => {
    const scout = this.availableScoutVessel();
    const baseChance = 0.65;
    if (scout) {
      let chance = baseChance + (scout.level - 1) * 0.05;
      if (scout.abilities.includes('DEEP_SCAN')) {
        chance += 0.1;
      }
      return Math.min(1, chance);
    }
    return baseChance;
  });

  openConstructionPanel() {
    this.setActivePanel.emit('CONSTRUCT');
  }

  onDispatch() {
    const hex = this.selectedHex();
    const daughter = this.availableServerDaughter();
    if (hex && daughter) {
      this.dispatchEntity.emit({ entityId: daughter.id, hexId: hex.id });
    }
  }

  onRecall() {
    const hex = this.selectedHex();
    if (hex) {
      this.recallEntity.emit(hex.id);
    }
  }

  onExtraction() {
    const hex = this.selectedHex();
    if (hex) {
      this.initiateExtraction.emit(hex);
    }
  }

  onConversion() {
    const hex = this.selectedHex();
    if (hex) {
      this.initiateConversion.emit(hex);
    }
  }

  onScout() {
    const hex = this.selectedHex();
    if (hex) {
      this.scoutHex.emit(hex);
    }
  }

  onOverclock() {
    this.activateCoreOverclock.emit();
  }
}
