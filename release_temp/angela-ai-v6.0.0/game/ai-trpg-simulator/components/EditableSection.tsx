
import React from 'react';
import { SmallLoadingSpinner } from './icons';

interface EditableSectionProps {
    title: string;
    content: string;
    isLoading: boolean;
}

const EditableSection: React.FC<EditableSectionProps> = ({ title, content, isLoading }) => {
    return (
        <details className="bg-gray-900/50 rounded-lg border border-gray-700" open>
            <summary className="p-3 cursor-pointer font-semibold text-gray-200 flex justify-between items-center">
                {title}
                {isLoading && <SmallLoadingSpinner />}
            </summary>
            <div className="p-3 border-t border-gray-700">
                <p className="whitespace-pre-wrap text-gray-300">{content}</p>
            </div>
        </details>
    );
};

export default EditableSection;
