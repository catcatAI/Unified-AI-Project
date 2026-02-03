import { Pipe, PipeTransform } from '@angular/core';
import { TranslationService } from '../services/translation.service';

@Pipe({
  name: 'translate',
  standalone: true,
  pure: false // This makes the pipe re-evaluate when the language signal changes
})
export class TranslatePipe implements PipeTransform {

  constructor(private translationService: TranslationService) {}

  transform(key: string, params?: Record<string, any>): string {
    return this.translationService.translate(key, params);
  }
}
