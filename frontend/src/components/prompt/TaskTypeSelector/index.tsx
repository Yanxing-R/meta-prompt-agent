import React from 'react';
import { SPECIFIC_TASK_TYPES, DEFAULT_TASK_TYPE } from '../../../utils/constants';
import { ChevronDownIcon } from '../../../components/icons';
import './styles.css';

interface TaskTypeSelectorProps {
  selectedTaskType: string | null;
  onTaskTypeSelect: (taskValue: string) => void;
  toggleTaskTypeDropdown: (index: number) => void;
  taskTypes: Array<{
    label: string;
    value: string;
    Icon: React.FC;
    isDropdownOpen?: boolean;
  }>;
}

const TaskTypeSelector: React.FC<TaskTypeSelectorProps> = ({
  selectedTaskType,
  onTaskTypeSelect,
  toggleTaskTypeDropdown,
  taskTypes
}) => {
  return (
    <div className="task-type-selector">
      <span className="task-type-label">任务类型:</span>
      
      <div className="task-types-container">
        <div 
          className={`task-type-button ${!selectedTaskType ? 'selected' : ''}`}
          onClick={() => onTaskTypeSelect(DEFAULT_TASK_TYPE)}
        >
          {DEFAULT_TASK_TYPE}
        </div>
        
        {taskTypes.map((task, index) => (
          <div className="task-type-item" key={task.value}>
            <div 
              className={`task-type-button ${selectedTaskType === task.value ? 'selected' : ''}`}
              onClick={() => onTaskTypeSelect(task.value)}
            >
              <task.Icon />
              <span>{task.label}</span>
            </div>
            
            {task.isDropdownOpen && (
              <div className="task-type-dropdown">
                <div className="task-type-dropdown-content">
                  {task.value}
                </div>
                <div className="task-type-dropdown-arrow" />
              </div>
            )}
            
            <ChevronDownIcon 
              className={`dropdown-icon ${task.isDropdownOpen ? 'open' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                toggleTaskTypeDropdown(index);
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskTypeSelector; 