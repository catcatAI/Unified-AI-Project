import { Component, ChangeDetectionStrategy, input, output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Game } from '../../models/game.model';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-m6-review-modal',
  templateUrl: './m6-review-modal.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, TranslatePipe],
})
export class M6ReviewModalComponent {
  isVisible = input.required<boolean>();
  m6Security = input.required<number>();
  confirm = output<void>();
  cancel = output<void>();

  onConfirm(): void {
    this.confirm.emit();
  }

  onCancel(): void {
    this.cancel.emit();
  }
}
