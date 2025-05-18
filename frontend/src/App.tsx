// frontend/src/App.tsx
import { useState, useEffect, useRef } from 'react';
import './App.css'; 
import thinkTwiceLogo from './assets/think-twice-logo.png'; // 1. 确保Logo图片已导入

// SVG 图标组件 - 发送箭头
const CreativeSendIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="24" 
    height="24" 
    viewBox="0 0 24 24" 
    fill="currentColor"
    className="send-icon"
  >
    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
  </svg>
);

// SVG 图标组件 - 停止
const StopIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="20" 
    height="20"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="stop-icon"
  >
    <rect x="6" y="6" width="12" height="12"></rect>
  </svg>
);

// 任务类型图标
const ResearchIcon = () => ( 
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
);
const ImageIcon = () => ( 
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
);
const CodeIcon = () => ( 
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
);

const SPECIFIC_TASK_TYPES = [
  { label: "研究", value: "深度研究", Icon: ResearchIcon },
  { label: "图像", value: "图像生成", Icon: ImageIcon },
  { label: "代码", value: "代码生成", Icon: CodeIcon },
];
const DEFAULT_TASK_TYPE = "通用/问答";

function App() {
  const [rawRequest, setRawRequest] = useState<string>('');
  const [p1Prompt, setP1Prompt] = useState<string>('');     
  const [isLoading, setIsLoading] = useState<boolean>(false); 
  const [error, setError] = useState<string | null>(null);   
  const [showResultAnimation, setShowResultAnimation] = useState<boolean>(false); 
  const [showIntro, setShowIntro] = useState<boolean>(true); 
  const [selectedTaskType, setSelectedTaskType] = useState<string | null>(SPECIFIC_TASK_TYPES[0].value); 

  const abortControllerRef = useRef<AbortController | null>(null);

  const handleSubmit = async () => {
    if (!rawRequest.trim()) {
      setError('请输入您的初步请求！');
      setP1Prompt(''); 
      setShowResultAnimation(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setP1Prompt(''); 
    setShowResultAnimation(false); 
    setShowIntro(false); 

    const taskTypeToSend = selectedTaskType || DEFAULT_TASK_TYPE;

    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      const response = await fetch('http://localhost:8000/generate-simple-p1', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          raw_request: rawRequest,
          task_type: taskTypeToSend 
        }),
        signal: signal, 
      });

      if (signal.aborted) { 
        console.log("Fetch aborted by user");
        setError("请求已取消。");
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP错误: ${response.status}` }));
        throw new Error(errorData.detail || `请求失败，状态码: ${response.status}`);
      }

      const data = await response.json();
      if (data.p1_prompt) {
        setP1Prompt(data.p1_prompt);
      } else {
        throw new Error('从API返回的数据格式不正确，缺少p1_prompt字段。');
      }

    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        console.log('Fetch aborted by user (in catch)');
        setError('请求已取消。');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('发生未知错误');
      }
      console.error('API调用失败:', err);
      setP1Prompt(''); 
      setShowResultAnimation(false);
    } finally {
      if (!signal.aborted) { 
        setIsLoading(false);
      }
      abortControllerRef.current = null; 
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort(); 
      setIsLoading(false); 
      setError("用户已取消请求。"); 
      console.log("Stop button clicked, aborting fetch.");
    }
  };

  const handleTaskTypeSelect = (taskValue: string) => {
    if (selectedTaskType === taskValue) {
      setSelectedTaskType(null);
    } else {
      setSelectedTaskType(taskValue);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !isLoading) {
      event.preventDefault(); 
      handleSubmit(); 
    }
  };

  useEffect(() => {
    if (p1Prompt) {
      const timer = setTimeout(() => {
        setShowResultAnimation(true); 
      }, 50); 
      return () => clearTimeout(timer);
    } else {
      setShowResultAnimation(false);
    }
  }, [p1Prompt]); 

  return (
    <>
      <div className="page-title-fixed">
        {/* 2. 将Logo图片放在文字标题之前 */}
        <img src={thinkTwiceLogo} alt="Think Twice Logo" className="page-title-logo" />
        <span className="page-title-text">Think Twice</span>
      </div>

      <div className="app-container">
        {showIntro && (
          <div className="intro-section">
            <h2>欢迎使用 Think Twice!</h2>
            <p>
              这是一个旨在提升您思考深度与提问技巧的智能伙伴。
              它不仅能帮助您梳理和完善自身的想法，更能引导您向大型语言模型 (LLM) 提出更精准、更有效的问题，从而开启更高质量的AI对话与成果。
            </p>
            <p>
              <strong>如何使用:</strong>
            </p>
            <ul>
              <li>在下方的输入框左侧选择一个任务场景（可选）。</li>
              <li>输入您对AI的初步想法或问题。</li>
              <li>点击发送按钮（或按Enter键）。</li>
            </ul>
             <p>
              <strong>示例 - 原始请求:</strong> "我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战" <br />
              <strong>可能的优化方向:</strong> "针对上述请求，Think Twice 可能会引导您思考：您想了解的是理论综述、具体方法的比较、还是当前挑战的解决方案？希望输出的格式是研究大纲、解释性段落还是问题列表？目标受众是初学者还是领域专家？" <br />
            </p>
          </div>
        )}
        
        <div className="input-area-container"> 
          <div className="task-buttons-sidebar"> 
            {SPECIFIC_TASK_TYPES.map((task) => (
              <button
                key={task.value}
                className={`task-type-button ${selectedTaskType === task.value ? 'active' : ''}`}
                onClick={() => handleTaskTypeSelect(task.value)}
                title={task.label}
              >
                <task.Icon /> 
                <span className="task-button-label">{task.label}</span> 
              </button>
            ))}
          </div>
          <div className="main-input-and-send-wrapper"> 
            <textarea
              value={rawRequest}
              onChange={(e) => setRawRequest(e.target.value)}
              onKeyPress={handleKeyPress} 
              placeholder="我想了解中短期天气、S2S及年际预报的模式初始化理论、方法与挑战"
              rows={4} 
              disabled={isLoading}
            />
            <button 
              className={`send-button ${isLoading ? 'loading' : ''}`} 
              onClick={isLoading ? handleStop : handleSubmit} 
              disabled={!isLoading && !rawRequest.trim()} 
              title={isLoading ? "停止生成" : "优化提示"} 
            >
              {isLoading ? (
                <StopIcon /> 
              ) : (
                <CreativeSendIcon /> 
              )}
            </button>
          </div>
        </div>

        {error && <p className="error-message">{error}</p>} 
        
        <div 
          className={`
            result-section 
            ${showResultAnimation ? 'visible' : ''}
            ${!p1Prompt && !isLoading && !error && !showIntro ? 'empty-placeholder' : ''} 
          `}
        >
          {p1Prompt ? (
            <>
              <h2>优化后的提示:</h2>
              <pre>{p1Prompt}</pre>
            </>
          ) : (
            !isLoading && !error && !showIntro && <p>优化后的提示将显示在此处...</p>
          )}
        </div>
      </div>
    </>
  );
}

export default App;



