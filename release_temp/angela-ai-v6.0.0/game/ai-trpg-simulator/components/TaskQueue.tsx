import React from 'react';
import { Task } from '../types';
import { useI18n } from '../context/i18n';
import { SmallLoadingSpinner } from './icons';

interface TaskQueueProps {
    tasks: Task[];
    isBusy: boolean;
}

const TaskQueue: React.FC<TaskQueueProps> = ({ tasks, isBusy }) => {
    const { t } = useI18n();

    if (tasks.length === 0) {
        return null;
    }

    return (
        <div>
            <h2 className="text-lg font-bold text-gray-300 border-b-2 border-gray-700 pb-2 mb-3">{t('taskQueue.title')}</h2>
            <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700 space-y-2 max-h-48 overflow-y-auto scrollbar-thin">
                {tasks.map((task, index) => {
                    const status = (index === 0 && isBusy) ? 'in-progress' : task.status;
                    return (
                        <div key={task.id} className="flex items-center gap-3 p-2 bg-gray-900/50 rounded-md">
                            {status === 'in-progress' && <div className="w-5 h-5 flex-shrink-0"><SmallLoadingSpinner /></div>}
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-gray-200 truncate">{task.description}</p>
                                <p className="text-xs text-gray-400 capitalize">{status}</p>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    );
};

export default TaskQueue;