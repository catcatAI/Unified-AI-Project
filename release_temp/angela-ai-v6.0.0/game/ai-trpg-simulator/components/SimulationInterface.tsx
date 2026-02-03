import React, { useRef } from 'react';

interface SimulationInterfaceProps {
    resources: Record<string, number>;
    choices: string[];
    onChoice: (choice: string) => void;
    isBusy: boolean;
}

const SimulationInterface: React.FC<SimulationInterfaceProps> = ({ resources, choices, onChoice, isBusy }) => {
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
             <div className="bg-yellow-900/20 p-2 rounded-lg border border-yellow-700/50">
                <div className="flex justify-around items-center mb-2 p-1 bg-black/20 rounded-md">
                    {Object.entries(resources).map(([key, value]) => (
                        <div key={key} className="text-center">
                            <p className="text-xs text-yellow-300 capitalize">{key}</p>
                            <p className="text-lg font-bold text-white">{value}</p>
                        </div>
                    ))}
                </div>
                <div className="grid grid-cols-1 gap-2">
                    {choices.map((choice, index) => (
                        <button
                            key={index}
                            onClick={() => handleChoice(choice)}
                            disabled={isBusy}
                            className="bg-yellow-800/50 hover:bg-yellow-700/70 text-white font-semibold py-2 px-3 rounded-md transition-colors text-left active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {choice}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default SimulationInterface;
