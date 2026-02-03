import { Injectable, signal, effect } from '@angular/core';
import { Game } from '../models/game.model';
import { translations } from '../i18n/translations';

@Injectable({
  providedIn: 'root',
})
export class TranslationService {
  currentLanguage = signal<Game.Language>('en');

  constructor() {
    const savedLang = localStorage.getItem('aethergenesis_lang') as Game.Language;
    if (savedLang && (savedLang === 'en' || savedLang === 'zh')) {
      this.currentLanguage.set(savedLang);
    }

    effect(() => {
      localStorage.setItem('aethergenesis_lang', this.currentLanguage());
    });
  }

  setLanguage(lang: Game.Language): void {
    this.currentLanguage.set(lang);
  }

  translate(key: string, params: Record<string, any> = {}): string {
    const lang = this.currentLanguage();
    const translationSet = translations[lang] || translations['en'];
    
    let translatedText = key.split('.').reduce((obj, k) => obj && obj[k], translationSet as any);

    if (typeof translatedText !== 'string') {
      console.warn(`Translation key not found: ${key}`);
      return key;
    }

    for (const param in params) {
      translatedText = translatedText.replace(new RegExp(`{{${param}}}`, 'g'), params[param]);
    }

    return translatedText;
  }
}
