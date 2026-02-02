

import { Component, ChangeDetectionStrategy, input, output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-hex-grid',
  templateUrl: './hex-grid.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class HexGridComponent {
  mapData = input.required<Game.Hex[][]>();
  selectedHex = input<Game.Hex | null>();
  hexSelected = output<Game.Hex>();

  selectHex(hex: Game.Hex) {
    this.hexSelected.emit(hex);
  }

  getHexClasses(hex: Game.Hex): string {
    if (hex.constructionProgress) {
        return 'bg-orange-900/60 border-yellow-500/80 animate-pulse';
    }
    const typeColors: { [key in Game.HexType]: string } = {
        'Resource': 'bg-green-800/60 border-green-500/60',
        'Refinery': 'bg-yellow-800/60 border-yellow-500/60',
        'ASI_Core': 'bg-red-900/80 border-red-500/60',
        'Empty': 'bg-gray-800/60 border-slate-600',
        'Server_Farm': 'bg-blue-800/60 border-blue-500/60',
        'Habitation_Dome': 'bg-teal-800/60 border-teal-500/60'
    };
    return typeColors[hex.type];
  }

}
