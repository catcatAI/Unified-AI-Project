import { Component, ChangeDetectionStrategy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';

import { GameStateService } from './services/game-state.service';
import { TranslationService } from './services/translation.service';
import { Game } from './models/game.model';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { HexGridComponent } from './components/hex-grid/hex-grid.component';
import { ResourceBarComponent } from './components/resource-bar/resource-bar.component';
import { ActionPanelComponent } from './components/action-panel/action-panel.component';
import { EventLogComponent } from './components/event-log/event-log.component';
import { MajorEventModalComponent } from './components/major-event-modal/major-event-modal.component';
import { M6ReviewModalComponent } from './components/m6-review-modal/m6-review-modal.component';
import { GameEndModalComponent } from './components/game-end-modal/game-end-modal.component';
import { TranslatePipe } from './pipes/translate.pipe';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    SidebarComponent,
    HexGridComponent,
    ResourceBarComponent,
    ActionPanelComponent,
    EventLogComponent,
    MajorEventModalComponent,
    M6ReviewModalComponent,
    GameEndModalComponent,
    TranslatePipe
  ],
  host: {
    '(window:mousemove)': 'onPanMove($event)',
    '(window:mouseup)': 'onPanEnd()',
    '(window:touchmove)': 'onPanMove($event)',
    '(window:touchend)': 'onPanEnd()',
  }
})
export class AppComponent {
  gameStateService = inject(GameStateService);
  translationService = inject(TranslationService);
  
  isGameStarted = signal(false);
  isSidebarOpen = signal(false);

  coreState = this.gameStateService.coreState;
  resourceState = this.gameStateService.resourceState;
  mapData = this.gameStateService.mapData;
  events = this.gameStateService.events;
  entities = this.gameStateService.entities;
  gameSpeed = this.gameStateService.gameSpeed;
  isGeneratingEvent = this.gameStateService.isGeneratingEvent;
  currentMajorEvent = this.gameStateService.currentMajorEvent;
  gameEndState = this.gameStateService.gameEndState;
  timedActions = this.gameStateService.timedActions;
  overclock = this.gameStateService.overclock;
  
  selectedHex = signal<Game.Hex | null>(null);
  activePanel = signal<Game.ActivePanel>('M_CORE');
  detailedEntity = signal<Game.Entity | null>(null);
  
  pendingMValueUpgrade = this.gameStateService.pendingMValueUpgrade;
  isM6ReviewVisible = signal(false);

  currentLanguage = this.translationService.currentLanguage;

  zoomLevel = signal(1);
  pan = signal({ x: 0, y: 0 });
  isPanning = signal(false);
  panStart = { x: 0, y: 0 };

  mapTransform = computed(() => {
    const panState = this.pan();
    const scale = this.zoomLevel();
    return `scale(${scale}) translate(${panState.x}px, ${panState.y}px)`;
  });

  startGame(): void {
    this.isGameStarted.set(true);
    this.gameStateService.beginGameLoops();
  }
  
  toggleSidebar(state?: boolean): void {
    this.isSidebarOpen.set(state ?? !this.isSidebarOpen());
  }

  onSetLanguage(lang: Game.Language): void {
    this.translationService.setLanguage(lang);
  }

  zoomIn(): void {
    this.zoomLevel.update(level => Math.min(2, level + 0.1));
  }
  
  zoomOut(): void {
    this.zoomLevel.update(level => Math.max(0.5, level - 0.1));
  }
  
  resetView(): void {
    this.zoomLevel.set(1);
    this.pan.set({ x: 0, y: 0 });
  }

  onPanStart(event: MouseEvent | TouchEvent): void {
    if (event instanceof MouseEvent && event.button !== 0) return;
    
    this.isPanning.set(true);
    const point = event instanceof MouseEvent ? event : event.touches[0];
    this.panStart = { x: point.clientX / this.zoomLevel() - this.pan().x, y: point.clientY / this.zoomLevel() - this.pan().y };
    event.preventDefault();
  }

  onPanMove(event: MouseEvent | TouchEvent): void {
    if (!this.isPanning()) return;

    const point = event instanceof MouseEvent ? event : event.touches[0];
    this.pan.set({
      x: point.clientX / this.zoomLevel() - this.panStart.x,
      y: point.clientY / this.zoomLevel() - this.panStart.y
    });

    if (event instanceof TouchEvent) {
      event.preventDefault();
    }
  }

  onPanEnd(): void {
    this.isPanning.set(false);
  }

  onHexSelected(hex: Game.Hex): void {
    this.selectedHex.set(hex);
  }

  onSetActivePanel(panel: Game.ActivePanel): void {
    this.activePanel.set(panel);
    if (panel !== 'ENTITY_DETAILS') {
        this.detailedEntity.set(null);
    }
  }

  onShowEntityDetails(entity: Game.Entity): void {
      this.detailedEntity.set(entity);
      this.activePanel.set('ENTITY_DETAILS');
  }

  onClearEntityDetails(): void {
      this.detailedEntity.set(null);
      this.activePanel.set('ENTITY_ROSTER');
  }

  onUnlockAbility(event: { entityId: number, abilityId: Game.AbilityId }): void {
      this.gameStateService.unlockEntityAbility(event.entityId, event.abilityId);
      // Refresh detailed entity to show updated state
      const currentId = this.detailedEntity()?.id;
      if (currentId) {
          this.detailedEntity.set(this.entities().find(e => e.id === currentId) ?? null);
      }
  }

  onBuildStructure(structureType: Game.StructureType): void {
    const hex = this.selectedHex();
    if (hex) {
      this.gameStateService.buildStructure(structureType, hex);
    } else {
      this.gameStateService.addEvent('events.noHexSelected', 'warning');
    }
  }

  onDispatchEntity(event: { entityId: number, hexId: string }): void {
    this.gameStateService.dispatchEntity(event.entityId, event.hexId);
  }

  onRecallEntity(hexId: string): void {
    this.gameStateService.recallEntity(hexId);
  }

  onInitiateExtraction(hex: Game.Hex): void {
    this.gameStateService.initiateExtraction(hex);
  }

  onInitiateConversion(hex: Game.Hex): void {
    this.gameStateService.initiateConversion(hex);
  }

  onSetGameSpeed(speed: Game.GameSpeed): void {
    this.gameStateService.setGameSpeed(speed);
  }

  onRequestGeminiEvent(): void {
    this.gameStateService.requestGeminiEvent();
  }

  requestMValueUpgrade(mValueKey: Game.MValueKey): void {
    const success = this.gameStateService.requestMValueUpgrade(mValueKey);
    if (success) {
      this.isM6ReviewVisible.set(true);
    }
  }

  onConfirmMValueUpgrade(): void {
    this.gameStateService.confirmMValueUpgrade();
    this.isM6ReviewVisible.set(false);
  }

  onCancelMValueUpgrade(): void {
    this.gameStateService.cancelMValueUpgrade();
    this.isM6ReviewVisible.set(false);
  }

  onManifestNewEntity(entityType: Game.EntityType): void {
    this.gameStateService.manifestNewEntity(entityType);
  }

  onScoutHex(hex: Game.Hex): void {
    this.gameStateService.scoutHex(hex);
  }
  
  onActivateCoreOverclock(): void {
    this.gameStateService.activateCoreOverclock();
  }

  onDismissMajorEvent(): void {
    this.gameStateService.dismissMajorEvent();
  }

  onConvertForExpansion(): void {
    this.gameStateService.convertForExpansion();
  }

  onExpandGrid(): void {
    this.gameStateService.expandPlanetaryGrid();
  }
  
  onRestartGame(): void {
    this.gameStateService.restartGame();
    this.isGameStarted.set(false);
  }
}
