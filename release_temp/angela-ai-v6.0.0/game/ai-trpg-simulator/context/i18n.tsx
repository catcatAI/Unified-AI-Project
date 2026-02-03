import React, { createContext, useContext, ReactNode, useCallback, useEffect, useState, useMemo } from 'react';
import { useSettings } from './settings';

export type Locale = 'en' | 'zh';

interface I18nContextType {
  locale: Locale;
  t: (key: string, replacements?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

const translations: Record<string, any> = {};

const InitialLoader: React.FC = () => (
    <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-100"></div>
    </div>
);

export const I18nProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { locale } = useSettings();
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const fetchTranslations = async () => {
      try {
        const [enResponse, zhResponse] = await Promise.all([
          fetch('./locales/en.json'),
          fetch('./locales/zh.json')
        ]);
        if (!enResponse.ok || !zhResponse.ok) {
            throw new Error('Network response was not ok');
        }
        translations.en = await enResponse.json();
        translations.zh = await zhResponse.json();
        setIsLoaded(true);
      } catch (error) {
        console.error("Failed to load translation files:", error);
      }
    };
    fetchTranslations();
  }, []);

  const t = useCallback((key: string, replacements?: Record<string, string | number>): string => {
    if (!isLoaded) return key;
    
    const findTranslation = (lang: Locale, translationKey: string): string | undefined => {
        const keys = translationKey.split('.');
        let result: any = translations[lang];
        for (const k of keys) {
            const index = parseInt(k, 10);
            if (!isNaN(index) && Array.isArray(result)) {
                result = result?.[index];
            } else {
                result = result?.[k];
            }
            if (result === undefined) return undefined;
        }
        // Ensure we return a string, not an object/array
        if (typeof result === 'string') {
            return result;
        }
        // If the path leads to an object (e.g., a missing final key), return undefined.
        return undefined;
    };
    
    let result = findTranslation(locale, key) ?? findTranslation('en', key) ?? key;

    if (replacements) {
        Object.keys(replacements).forEach(rKey => {
            const regex = new RegExp(`{${rKey}}`, 'g');
            result = result.replace(regex, String(replacements[rKey]));
        });
    }
    
    return result;
  }, [locale, isLoaded]);

  const value = useMemo(() => ({ locale, t }), [locale, t]);

  if (!isLoaded) {
    return <InitialLoader />;
  }

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};
