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

// 新增：信息图标
const InfoIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="16" 
    height="16" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="16" x2="12" y2="12"></line>
    <line x1="12" y1="8" x2="12.01" y2="8"></line>
  </svg>
);

// 新增：设置图标
const SettingsIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="16" 
    height="16" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="3"></circle>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
  </svg>
);

// 新增：星星图标
const StarIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="18" 
    height="18" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);

// 新增：填充星星图标
const StarFilledIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="18" 
    height="18" 
    viewBox="0 0 24 24" 
    fill="currentColor" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
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

// 定义系统信息类型
interface SystemInfo {
  active_llm_provider: string;
  model_name: string;
  available_providers: string[];
  version: string;
  structured_templates?: string[];
}

// 定义生成提示词的响应类型
interface SimplePromptResponse {
  p1_prompt: string;
}

interface AdvancedPromptResponse {
  final_prompt: string;
  intermediate_steps?: {
    original_prompt: string;
    corrected_prompt: string;
    correction_explanation: string;
  }[];
}

function App() {
  const [rawRequest, setRawRequest] = useState<string>('');
  const [p1Prompt, setP1Prompt] = useState<string>('');     
  const [isLoading, setIsLoading] = useState<boolean>(false); 
  const [error, setError] = useState<string | null>(null);   
  const [showResultAnimation, setShowResultAnimation] = useState<boolean>(false); 
  const [showIntro, setShowIntro] = useState<boolean>(true); 
  const [selectedTaskType, setSelectedTaskType] = useState<string | null>(SPECIFIC_TASK_TYPES[0].value);
  
  // 新增状态
  const [advancedMode, setAdvancedMode] = useState<boolean>(false);
  const [selfCorrection, setSelfCorrection] = useState<boolean>(true);
  const [recursionDepth, setRecursionDepth] = useState<number>(2);
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [showFeedback, setShowFeedback] = useState<boolean>(false);
  const [showTermExplainer, setShowTermExplainer] = useState<boolean>(false);
  const [termToExplain, setTermToExplain] = useState<string>('');
  const [termExplanation, setTermExplanation] = useState<string>('');
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [showSystemInfo, setShowSystemInfo] = useState<boolean>(false);
  const [feedbackRating, setFeedbackRating] = useState<number>(0);
  const [feedbackComment, setFeedbackComment] = useState<string>('');
  const [selectedText, setSelectedText] = useState<string>('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);
  const [showIntermediateSteps, setShowIntermediateSteps] = useState<boolean>(false);
  const [intermediateSteps, setIntermediateSteps] = useState<any[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const resultRef = useRef<HTMLPreElement>(null);

  // 获取系统信息
  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        const response = await fetch('/api/system/info');
        if (response.ok) {
          const data = await response.json();
          setSystemInfo(data);
        }
      } catch (err) {
        console.error('获取系统信息失败:', err);
      }
    };
    
    fetchSystemInfo();
  }, []);

  // 文本选择事件处理
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      if (selection && selection.toString().trim()) {
        setSelectedText(selection.toString().trim());
      } else {
        setSelectedText('');
      }
    };

    document.addEventListener('mouseup', handleSelection);
    document.addEventListener('keyup', handleSelection);

    return () => {
      document.removeEventListener('mouseup', handleSelection);
      document.removeEventListener('keyup', handleSelection);
    };
  }, []);

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
    setIntermediateSteps([]);

    const taskTypeToSend = selectedTaskType || DEFAULT_TASK_TYPE;

    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      // 根据是否是高级模式选择不同的API端点
      const endpoint = advancedMode ? '/api/generate-advanced-prompt' : '/api/generate-simple-p1';
      const requestBody = advancedMode 
        ? {
            raw_request: rawRequest,
            task_type: taskTypeToSend,
            enable_self_correction: selfCorrection,
            max_recursion_depth: recursionDepth,
            template_name: null,
            template_variables: null
          }
        : {
            raw_request: rawRequest,
            task_type: taskTypeToSend
          };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
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
      
      // 根据高级模式处理不同的响应结构
      if (advancedMode) {
        const advancedData = data as AdvancedPromptResponse;
        setP1Prompt(advancedData.final_prompt);
        if (advancedData.intermediate_steps && advancedData.intermediate_steps.length > 0) {
          setIntermediateSteps(advancedData.intermediate_steps);
        }
      } else {
        const simpleData = data as SimplePromptResponse;
        setP1Prompt(simpleData.p1_prompt);
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

  // 解释术语
  const handleExplainTerm = async () => {
    if (!termToExplain || !p1Prompt) {
      setError('请选择要解释的术语并确保已生成提示词');
      return;
    }

    setIsLoading(true);
    setTermExplanation('');
    setError(null);

    try {
      const response = await fetch('/api/explain-term', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          term_to_explain: termToExplain,
          context_prompt: p1Prompt
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP错误: ${response.status}` }));
        throw new Error(errorData.detail || `请求失败，状态码: ${response.status}`);
      }

      const data = await response.json();
      setTermExplanation(data.explanation || '未能获取解释');
      setShowTermExplainer(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : '解释术语时发生未知错误');
    } finally {
      setIsLoading(false);
    }
  };

  // 提交反馈
  const handleSubmitFeedback = async () => {
    if (feedbackRating === 0) {
      setError('请选择评分');
      return;
    }

    if (!p1Prompt) {
      setError('没有可评价的提示词');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt_id: Date.now().toString(), // 简单生成ID
          original_request: rawRequest,
          generated_prompt: p1Prompt,
          rating: feedbackRating,
          comment: feedbackComment || undefined
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `请求失败，状态码: ${response.status}`);
      }

      setFeedbackSubmitted(true);
      setTimeout(() => {
        setShowFeedback(false);
        setFeedbackSubmitted(false);
        setFeedbackRating(0);
        setFeedbackComment('');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交反馈时发生未知错误');
    } finally {
      setIsLoading(false);
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
        <div className="page-title-left">
          <img src={thinkTwiceLogo} alt="Think Twice Logo" className="page-title-logo" />
          <span className="page-title-text">Think Twice</span>
        </div>
        
        <div className="tool-buttons">
          <button 
            className="tool-button" 
            onClick={() => setShowSettings(!showSettings)}
            title="设置"
          >
            <SettingsIcon />
          </button>
          <button 
            className="tool-button" 
            onClick={() => setShowSystemInfo(!showSystemInfo)}
            title="系统信息"
          >
            <InfoIcon />
          </button>
        </div>
      </div>

      <div className="app-container">
        {/* 设置面板 */}
        {showSettings && (
          <div className="settings-panel">
            <h3>高级设置</h3>
            <div className="settings-row">
              <label>
                <input 
                  type="checkbox" 
                  checked={advancedMode} 
                  onChange={(e) => setAdvancedMode(e.target.checked)} 
                />
                启用高级提示生成
              </label>
            </div>
            
            {advancedMode && (
              <>
                <div className="settings-row">
                  <label>
                    <input 
                      type="checkbox" 
                      checked={selfCorrection} 
                      onChange={(e) => setSelfCorrection(e.target.checked)} 
                    />
                    启用自我校正
                  </label>
                </div>
                <div className="settings-row">
                  <label htmlFor="recursion-depth">最大递归深度</label>
                  <select 
                    id="recursion-depth"
                    value={recursionDepth} 
                    onChange={(e) => setRecursionDepth(parseInt(e.target.value))}
                    aria-label="最大递归深度"
                  >
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                  </select>
                </div>
              </>
            )}
          </div>
        )}

        {/* 系统信息面板 */}
        {showSystemInfo && systemInfo && (
          <div className="system-info-panel">
            <h3>系统信息</h3>
            <div className="info-row">
              <span>当前LLM提供商:</span>
              <span>{systemInfo.active_llm_provider}</span>
            </div>
            <div className="info-row">
              <span>模型名称:</span>
              <span>{systemInfo.model_name}</span>
            </div>
            <div className="info-row">
              <span>API版本:</span>
              <span>{systemInfo.version}</span>
            </div>
            <div className="info-row">
              <span>可用提供商:</span>
              <span>{systemInfo.available_providers.join(', ')}</span>
            </div>
            {systemInfo.structured_templates && systemInfo.structured_templates.length > 0 && (
              <div className="info-row">
                <span>可用模板:</span>
                <span>{systemInfo.structured_templates.join(', ')}</span>
              </div>
            )}
          </div>
        )}

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
            
            {/* 高级模式指示器 */}
            {advancedMode && (
              <div className="mode-indicator">高级模式</div>
            )}
          </div>
          <div className="main-input-and-send-wrapper"> 
            <textarea
              ref={textareaRef}
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
              <div className="result-header">
                <h2>优化后的提示:</h2>
                
                <div className="result-tools">
                  {selectedText && (
                    <button 
                      className="tool-button"
                      onClick={() => {
                        setTermToExplain(selectedText);
                        handleExplainTerm();
                      }}
                      title="解释所选术语"
                    >
                      解释"{selectedText.length > 10 ? selectedText.substring(0, 10) + '...' : selectedText}"
                    </button>
                  )}
                  {advancedMode && intermediateSteps.length > 0 && (
                    <button
                      className="tool-button"
                      onClick={() => setShowIntermediateSteps(!showIntermediateSteps)}
                      title={showIntermediateSteps ? "隐藏中间步骤" : "显示中间步骤"}
                    >
                      {showIntermediateSteps ? "隐藏步骤" : "显示步骤"}
                    </button>
                  )}
                  <button 
                    className="tool-button"
                    onClick={() => setShowFeedback(!showFeedback)}
                    title="提供反馈"
                  >
                    反馈
                  </button>
                </div>
              </div>
              
              {/* 显示中间步骤 */}
              {showIntermediateSteps && intermediateSteps.length > 0 && (
                <div className="intermediate-steps">
                  <h3>自我校正步骤:</h3>
                  {intermediateSteps.map((step, index) => (
                    <div key={index} className="correction-step">
                      <div className="step-number">步骤 {index + 1}</div>
                      <div className="step-explanation">{step.correction_explanation}</div>
                      <div className="before-after">
                        <div className="before">
                          <div className="label">原始:</div>
                          <div className="content">{step.original_prompt}</div>
                        </div>
                        <div className="after">
                          <div className="label">修正:</div>
                          <div className="content">{step.corrected_prompt}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              <pre ref={resultRef}>{p1Prompt}</pre>
              
              {/* 术语解释器 */}
              {showTermExplainer && termExplanation && (
                <div className="term-explainer">
                  <div className="term-explainer-header">
                    <h3>"{termToExplain}" 的解释:</h3>
                    <button 
                      className="close-button"
                      onClick={() => setShowTermExplainer(false)}
                    >
                      ×
                    </button>
                  </div>
                  <p>{termExplanation}</p>
                </div>
              )}
              
              {/* 反馈表单 */}
              {showFeedback && (
                <div className="feedback-form">
                  <div className="feedback-header">
                    <h3>您对生成的提示词满意吗？</h3>
                    <button 
                      className="close-button"
                      onClick={() => setShowFeedback(false)}
                    >
                      ×
                    </button>
                  </div>
                  
                  {feedbackSubmitted ? (
                    <div className="feedback-success">
                      感谢您的反馈！
                    </div>
                  ) : (
                    <>
                      <div className="rating-stars">
                        {[1, 2, 3, 4, 5].map((rating) => (
                          <button
                            key={rating}
                            className="star-button"
                            onClick={() => setFeedbackRating(rating)}
                            title={`${rating}星`}
                          >
                            {rating <= feedbackRating ? <StarFilledIcon /> : <StarIcon />}
                          </button>
                        ))}
                      </div>
                      <textarea
                        placeholder="您有什么建议或评论？（可选）"
                        value={feedbackComment}
                        onChange={(e) => setFeedbackComment(e.target.value)}
                        rows={3}
                      ></textarea>
                      <button 
                        className="submit-feedback-button"
                        onClick={handleSubmitFeedback}
                        disabled={feedbackRating === 0}
                      >
                        提交反馈
                      </button>
                    </>
                  )}
                </div>
              )}
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



