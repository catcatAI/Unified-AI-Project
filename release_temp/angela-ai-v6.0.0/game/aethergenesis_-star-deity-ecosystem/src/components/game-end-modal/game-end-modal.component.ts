import { Component, ChangeDetectionStrategy, input, output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-game-end-modal',
  templateUrl: './game-end-modal.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class GameEndModalComponent {
  endState = input<Game.GameEndState | null>();
  restart = output<void>();
  
  onRestart(): void {
    this.restart.emit();
  }
}
