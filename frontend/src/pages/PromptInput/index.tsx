import React, { useState } from 'react';
import PromptArea from '../../components/prompt/PromptArea';
import TaskTypeSelector from '../../components/prompt/TaskTypeSelector';
import './styles.css';

interface PromptInputProps {
  onSubmit: (promptText: string, taskType: string) => void;
  isLoading: boolean;
}

const PromptInput: React.FC<PromptInputProps> = ({ 
  onSubmit, 
  isLoading 
}) => {
  const [promptText, setPromptText] = useState<string>('');
  const [selectedTaskType, setSelectedTaskType] = useState<string | null>(null);

  const handlePromptChange = (text: string) => {
    setPromptText(text);
  };

  const handleTaskTypeSelect = (taskType: string) => {
    setSelectedTaskType(taskType === selectedTaskType ? null : taskType);
  };

  const handleSubmit = () => {
    if (promptText.trim()) {
      onSubmit(promptText, selectedTaskType || '通用/问答');
    }
  };

  return (
    <div className="prompt-input-page">
      <div className="prompt-input-container">
        <h2 className="prompt-input-title">优化你的AI提示词</h2>
        <p className="prompt-input-subtitle">输入你想要优化的提示词，我们将利用最佳实践对其进行改进</p>
        
        <TaskTypeSelector 
          selectedTaskType={selectedTaskType || ''} 
          onTaskTypeSelect={handleTaskTypeSelect} 
        />
        
        <PromptArea 
          promptText={promptText} 
          onPromptChange={handlePromptChange} 
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default PromptInput; 