import React from 'react';
import { useI18n } from '../context/i18n';
import { VideoIcon } from './icons';

interface ApiKeySelectorProps {
    onSelectKey: () => void;
}

const ApiKeySelector: React.FC<ApiKeySelectorProps> = ({ onSelectKey }) => {
    const { t } = useI18n();

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4" style={{ 
            backgroundImage: `radial-gradient(circle at top right, rgba(29, 78, 216, 0.15), transparent 40%), 
                              radial-gradient(circle at bottom left, rgba(107, 33, 168, 0.15), transparent 50%)` 
          }}>
            <div className="w-full max-w-lg mx-auto bg-gray-800 rounded-2xl shadow-lg p-8 border border-gray-700 text-center">
                <VideoIcon className="w-16 h-16 mx-auto text-indigo-400 mb-4" />
                <h1 className="text-3xl font-bold mb-2 text-gray-100">{t('videoGenerator.title')}</h1>
                <p className="text-gray-400 mb-6">{t('suite.settings.apiKeyDesc')}</p>

                <button 
                    onClick={onSelectKey}
                    className="w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 transition-colors text-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500"
                >
                    {t('suite.settings.selectApiKey')}
                </button>
                <p className="text-xs text-gray-500 mt-4">
                    For more information, see the{' '}
                    <a href="https://ai.google.dev/gemini-api/docs/billing" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">
                        billing documentation
                    </a>.
                </p>
            </div>
        </div>
    );
};

export default ApiKeySelector;
