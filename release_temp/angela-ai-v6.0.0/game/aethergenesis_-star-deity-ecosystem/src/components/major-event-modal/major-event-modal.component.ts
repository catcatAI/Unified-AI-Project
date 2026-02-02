
import { Component, ChangeDetectionStrategy, input, output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-major-event-modal',
  templateUrl: './major-event-modal.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class MajorEventModalComponent {
  event = input<Game.MajorGameEvent | null>();
  dismiss = output<void>();

  onDismiss(): void {
    this.dismiss.emit();
  }
}
