import { Component, ChangeDetectionStrategy, input, effect, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-resource-bar',
  templateUrl: './resource-bar.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class ResourceBarComponent {
  resourceState = input.required<Game.ResourceState>();
  
  changeStates = signal<Record<string, 'increment' | 'decrement'>>({});
  
  private previousState: Game.ResourceState | undefined;

  constructor() {
    effect(() => {
      const newState = this.resourceState();
      
      if (this.previousState) {
        const changes: Record<string, 'increment' | 'decrement'> = {};
        
        for (const key in newState) {
          const resKey = key as Game.ResourceKey;
          const oldAmount = this.previousState[resKey]?.amount;
          const newAmount = newState[resKey].amount;

          if (oldAmount !== undefined && newAmount !== oldAmount) {
            changes[resKey] = newAmount > oldAmount ? 'increment' : 'decrement';
          }
        }
        
        if (Object.keys(changes).length > 0) {
          this.changeStates.set(changes);
          setTimeout(() => this.changeStates.set({}), 500);
        }
      }
      
      this.previousState = JSON.parse(JSON.stringify(newState));
    }, { allowSignalWrites: true });
  }
}