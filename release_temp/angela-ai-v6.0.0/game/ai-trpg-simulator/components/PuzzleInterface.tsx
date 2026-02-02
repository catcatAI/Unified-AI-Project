import React, { useRef } from 'react';

interface PuzzleInterfaceProps {
    choices: string[];
    onChoice: (choice: string) => void;
    isBusy: boolean;
}

const PuzzleInterface: React.FC<PuzzleInterfaceProps> = ({ choices, onChoice, isBusy }) => {
    const debounceLock = useRef(false);

    const handleChoice = (choice: string) => {
        if (debounceLock.current || isBusy) return;
        debounceLock.current = true;
        onChoice(choice);
        setTimeout(() => {
            debounceLock.current = false;
        }, 500);
    };

    return (
        <div className="flex-shrink-0 p-2 border-t border-gray-700">
            <div className="bg-purple-900/20 p-2 rounded-lg border border-purple-700/50">
                 <div className="grid grid-cols-1 gap-2">
                    {choices.map((choice, index) => (
                        <button
                            key={index}
                            onClick={() => handleChoice(choice)}
                            disabled={isBusy}
                            className="bg-purple-800/50 hover:bg-purple-700/70 text-white font-semibold py-2 px-3 rounded-md transition-colors text-left active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {choice}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default PuzzleInterface;
