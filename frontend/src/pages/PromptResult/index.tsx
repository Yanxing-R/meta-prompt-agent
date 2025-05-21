import React, { useState } from 'react';
import './styles.css';
import Button from '../../components/common/Button';
import FeedbackForm from '../../components/prompt/FeedbackForm';
import { CopyIcon, CompareIcon, ArrowLeftIcon, PenIcon } from '../../components/icons';

interface PromptResultProps {
  optimizedPrompt: string;
  initialPrompt: string;
  onBackToInput: () => void;
  onViewSteps: () => void;
  onFeedbackSubmit: (rating: number, feedback: string) => Promise<void>;
}

const PromptResult: React.FC<PromptResultProps> = ({
  optimizedPrompt,
  initialPrompt,
  onBackToInput,
  onViewSteps,
  onFeedbackSubmit
}) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [improvementNotes, setImprovementNotes] = useState<string | null>(null);
  const [promptContent, setPromptContent] = useState('');

  // 当组件接收到优化后的提示词时解析它
  React.useEffect(() => {
    if (optimizedPrompt) {
      const result = parseOptimizedPrompt(optimizedPrompt);
      setPromptContent(result.promptContent);
      setImprovementNotes(result.improvementNotes);
    }
  }, [optimizedPrompt]);

  // 解析优化后的提示词，提取正文和改进说明
  const parseOptimizedPrompt = (fullPrompt: string): { promptContent: string; improvementNotes: string | null } => {
    const startMarker = "<<USER_COPY_PROMPT_START>>";
    const endMarker = "<<USER_COPY_PROMPT_END>>";
    
    // 提取标记之间的内容（如果有）
    if (fullPrompt.includes(startMarker) && fullPrompt.includes(endMarker)) {
      const startIndex = fullPrompt.indexOf(startMarker) + startMarker.length;
      const endIndex = fullPrompt.indexOf(endMarker, startIndex);
      
      if (startIndex > -1 && endIndex > startIndex) {
        // 如果存在标记，则提取内容
        return {
          promptContent: fullPrompt.substring(startIndex, endIndex).trim(),
          improvementNotes: fullPrompt.substring(0, fullPrompt.indexOf(startMarker)).trim()
        };
      }
    }
    
    // 如果没有标记，使用默认处理逻辑
    const lines = fullPrompt.split('\n');
    
    // 跳过可能的前缀行
    let contentStartIndex = 0;
    while (contentStartIndex < lines.length) {
      const line = lines[contentStartIndex].trim();
      if (line === '' || line.startsWith('#') || line.startsWith('主题') || line.startsWith('角色')) {
        contentStartIndex++;
      } else {
        break;
      }
    }
    
    // 如果内容很短，可能没有改进说明
    if (lines.length <= contentStartIndex + 3) {
      return { promptContent: fullPrompt.trim(), improvementNotes: null };
    }
    
    // 提取内容
    return {
      promptContent: lines.slice(contentStartIndex).join('\n').trim(),
      improvementNotes: null
    };
  };

  // 复制提示词到剪贴板
  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(promptContent).then(() => {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    });
  };

  // 切换反馈表单显示
  const handleToggleFeedback = () => {
    setShowFeedback(!showFeedback);
  };

  // 处理反馈提交
  const handleFeedbackSubmit = async (rating: number, feedback: string) => {
    await onFeedbackSubmit(rating, feedback);
    setShowFeedback(false);
  };

  return (
    <div className="prompt-result-page">
      <div className="result-container">
        <div className="result-header">
          <Button
            variant="outline"
            icon={<ArrowLeftIcon />}
            onClick={onBackToInput}
          >
            返回
          </Button>
          <h2 className="result-title">优化后的提示词</h2>
          <div className="result-actions">
            <Button
              variant="action"
              icon={<CompareIcon />}
              onClick={onViewSteps}
              title="查看自我校正与评估步骤"
            >
              查看评估
            </Button>
            <Button
              variant="action"
              icon={<PenIcon />}
              onClick={handleToggleFeedback}
              title="提供反馈"
            >
              提供反馈
            </Button>
          </div>
        </div>

        {improvementNotes && (
          <div className="improvement-notes">
            <h3 className="improvement-notes-title">改进说明</h3>
            <div className="improvement-notes-content">
              {improvementNotes}
            </div>
          </div>
        )}

        <div className="prompt-content-container">
          <div className="prompt-content-header">
            <h3 className="prompt-content-title">最终提示词</h3>
            <Button
              variant="action"
              icon={<CopyIcon />}
              onClick={handleCopyToClipboard}
              className={copySuccess ? 'btn-copy-success' : ''}
            >
              {copySuccess ? '已复制' : '复制提示词'}
            </Button>
          </div>
          <div className="prompt-content">
            <pre>{promptContent}</pre>
          </div>
        </div>

        {showFeedback && (
          <div className="feedback-section">
            <FeedbackForm onSubmit={handleFeedbackSubmit} onCancel={() => setShowFeedback(false)} />
          </div>
        )}
      </div>
    </div>
  );
};

export default PromptResult; 