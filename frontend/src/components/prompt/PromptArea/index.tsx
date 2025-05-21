import React, { useState, useRef, useEffect } from 'react';
import Button from '../../../components/common/Button';
import { CreativeSendIcon, StopIcon, CopyIcon } from '../../../components/icons';
import './styles.css';

interface PromptAreaProps {
  prompt: string;
  setPrompt: (value: string) => void;
  placeholder?: string;
  isLoading: boolean;
  optimizedPrompt?: string;
  improvementNotes?: string | null;
  isOptimized: boolean;
  handleSubmit: () => void;
  handleStop: () => void;
  handleKeyPress: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  handleCopyToClipboard: () => void;
  error?: string;
}

const PromptArea: React.FC<PromptAreaProps> = ({
  prompt,
  setPrompt,
  placeholder = '输入您想优化的提示词...',
  isLoading,
  optimizedPrompt,
  improvementNotes,
  isOptimized,
  handleSubmit,
  handleStop,
  handleKeyPress,
  handleCopyToClipboard,
  error
}) => {
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const resultAreaRef = useRef<HTMLTextAreaElement>(null);
  const notesAreaRef = useRef<HTMLDivElement>(null);
  
  // 自动调整文本域高度
  const adjustTextareaHeight = (textarea: HTMLTextAreaElement | null) => {
    if (!textarea) return;
    
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 400)}px`;
  };
  
  // 监听文本域内容变化，自动调整高度
  useEffect(() => {
    adjustTextareaHeight(textAreaRef.current);
  }, [prompt]);
  
  useEffect(() => {
    adjustTextareaHeight(resultAreaRef.current);
  }, [optimizedPrompt]);
  
  return (
    <div className="prompt-area">
      {/* 输入区域 */}
      {!isOptimized && (
        <div className="prompt-input-container">
          <label htmlFor="prompt-input" className="sr-only">提示词输入</label>
          <textarea
            id="prompt-input"
            ref={textAreaRef}
            className="prompt-textarea"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={placeholder}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
          />
          
          <div className="prompt-actions">
            {isLoading ? (
              <Button
                onClick={handleStop}
                variant="outline"
                icon={<StopIcon />}
              >
                停止
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                variant="primary"
                icon={<CreativeSendIcon />}
                disabled={!prompt.trim()}
              >
                优化
              </Button>
            )}
          </div>
          
          {error && <div className="prompt-error">{error}</div>}
        </div>
      )}
      
      {/* 结果展示区域 */}
      {isOptimized && optimizedPrompt && (
        <div className="prompt-result-container">
          <div className="prompt-result-header">
            <h3>优化后的提示词</h3>
            <Button
              onClick={handleCopyToClipboard}
              variant="outline"
              size="small"
              icon={<CopyIcon />}
            >
              复制
            </Button>
          </div>
          
          <label htmlFor="prompt-result" className="sr-only">优化后的提示词</label>
          <textarea
            id="prompt-result"
            ref={resultAreaRef}
            className="prompt-result-textarea"
            value={optimizedPrompt}
            readOnly
            aria-label="优化后的提示词"
          />
          
          {/* 改进说明区域 */}
          {improvementNotes && (
            <div className="prompt-improvement-notes-container">
              <h4 className="prompt-improvement-notes-title">改进说明</h4>
              <div 
                ref={notesAreaRef}
                className="prompt-improvement-notes"
              >
                {improvementNotes}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PromptArea; 