

import { Component, ChangeDetectionStrategy, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-event-log',
  templateUrl: './event-log.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class EventLogComponent {
  events = input.required<Game.GameEvent[]>();

  getEventTypeColor(type: Game.GameEvent['type']): string {
    switch (type) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'danger': return 'text-red-400 font-bold';
      case 'info': return 'text-sky-400';
      case 'system': return 'text-gray-500';
      default: return 'text-gray-300';
    }
  }
}
