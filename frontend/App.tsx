// frontend/src/App.tsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import './App.css'; 

// 导入组件
import Header from './components/layout/Header';
import PromptInput from './pages/PromptInput';
import PromptResult from './pages/PromptResult';
import StepsView from './pages/StepsView';
import SettingsPanel from './components/layout/SettingsPanel';

// --- SVG Icon Components ---
const CreativeSendIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="send-icon"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path></svg>);
const StopIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="stop-icon"><rect x="6" y="6" width="12" height="12"></rect></svg>);
const InfoIcon = ({ size = 16 }: { size?: number }) => (<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="info-icon"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>);
const SettingsIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="settings-icon"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>);
const StarIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>);
const StarFilledIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>);
const ChevronDownIcon = ({ className = "", onClick }: { className?: string, onClick?: (e: React.MouseEvent) => void }) => (<svg className={className} onClick={onClick} xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>);
const XIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>);
const MaximizeIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>);
const MinimizeIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path></svg>);
const CompareIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>);
const PenIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>);
const CopyIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>);
const ArrowLeftIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>);

// Task type icons
const ResearchIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>);
const ImageIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>);
const CodeIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>);
const VideoIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>);
const ChatbotIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>);
const WritingIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path><circle cx="11" cy="11" r="2"></circle></svg>);

// --- Type Definitions ---
interface ModelOption { name: string; value: string; provider: string; group: string; id?: string; }
interface ProviderOption { name: string; value: string; }
interface SystemInfo { active_llm_provider: string; model_name: string; available_providers: string[]; version: string; structured_templates?: string[]; available_models?: ModelOption[]; }
interface SimplePromptResponse { p1_prompt: string; }
interface ProcessedStep {
  stepNumber: number;
  promptBeforeEvaluation: string;
  evaluationReport: any;
  promptAfterRefinement: string;
  isExpanded?: boolean;
  scoreDetails?: {
    category: string;
    score: number;
    maxScore: number;
    comment?: string;
  }[];
  overallScore?: number;
  guidelines?: string;
  suggestions?: string;
}
interface AdvancedPromptResponseAPI { // Matches backend Pydantic model
  final_prompt: string;
  initial_prompt: string;
  evaluation_reports?: any[];
  refined_prompts?: string[];
  message?: string;
}

// --- Constants ---
const SPECIFIC_TASK_TYPES = [ { label: "研究", value: "深度研究", Icon: ResearchIcon }, { label: "图像", value: "图像生成", Icon: ImageIcon }, { label: "代码", value: "代码生成", Icon: CodeIcon }, { label: "视频", value: "视频生成", Icon: VideoIcon }, { label: "聊天", value: "聊天机器人", Icon: ChatbotIcon }, { label: "写作", value: "内容写作", Icon: WritingIcon }, ];
const DEFAULT_TASK_TYPE = "通用/问答";
const API_BASE_URL = ''; // 使用相对URL，与前端服务同源

// --- ToggleSwitch Component ---
const ToggleSwitch = ({ id, checked, onChange, label }: { id: string, checked: boolean, onChange: (checked: boolean) => void, label: string }) => ( <div className="toggle-switch-container"> <label htmlFor={id} className="toggle-switch-label">{label}</label> <label className="toggle-switch"> <input type="checkbox" id={id} checked={checked} onChange={(e) => onChange(e.target.checked)} /> <span className="slider round"></span> </label> </div> );

// --- 添加diff处理的辅助函数 ---
interface DiffPart {
  value: string;
  added?: boolean;
  removed?: boolean;
}

// 将两段文本分解为行进行比较
const compareTexts = (oldText: string, newText: string): DiffPart[][] => {
  // 将文本按行分割
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  // 使用diff库进行行级别的差异比较
  const diffResult = Diff.diffArrays(oldLines, newLines);
  
  // 转换diff结果以便于渲染
  const lineByLineDiff: DiffPart[][] = [];
  
  diffResult.forEach(part => {
    part.value.forEach(line => {
      const diffLine: DiffPart[] = [{
        value: line,
        added: part.added,
        removed: part.removed
      }];
      lineByLineDiff.push(diffLine);
    });
  });
  
  return lineByLineDiff;
};

// 进行字符级别的差异比较 (暂未使用，但保留为未来可能的功能)
// @ts-ignore - 未使用的函数，保留以待将来使用
const compareTextDetails = (oldText: string, newText: string): DiffPart[][] => {
  // 将文本按行分割
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  // 对每行文本进行字符级别比较
  const result: DiffPart[][] = [];
  
  // 使用diff库进行行级别的差异比较，找出哪些行被添加/删除/修改
  const lineDiff = Diff.diffArrays(oldLines, newLines);
  
  // 处理完全添加或删除的行
  lineDiff.forEach(part => {
    if (part.added || part.removed) {
      part.value.forEach(line => {
        result.push([{
          value: line,
          added: part.added,
          removed: part.removed
        }]);
      });
      } else {
      // 对未改变的行，仍然作为一行添加
      part.value.forEach(line => {
        result.push([{
          value: line
        }]);
      });
    }
  });
  
  return result;
};

// 对两段文本做单词级别的差异比较 (暂未使用，但保留为未来可能的功能)
// @ts-ignore - 未使用的函数，保留以待将来使用
const compareWordsInTexts = (oldText: string, newText: string): DiffPart[][] => {
  // 将文本按行分割
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  // 使用diff-match-patch算法进行单词级别的比较
  const diffResults: DiffPart[][] = [];
  
  // 获取两个文本共同的行
  const lineDiff = Diff.diffArrays(oldLines, newLines);
  const commonLines: number[][] = []; // [oldIndex, newIndex]
  
  let oldIndex = 0;
  let newIndex = 0;
  
  lineDiff.forEach(part => {
    if (part.added) {
      // 添加的行，只存在于新文本
      newIndex += part.count || 0;
    } else if (part.removed) {
      // 删除的行，只存在于旧文本
      oldIndex += part.count || 0;
    } else {
      // 共同的行
      for (let i = 0; i < (part.count || 0); i++) {
        commonLines.push([oldIndex + i, newIndex + i]);
      }
      oldIndex += part.count || 0;
      newIndex += part.count || 0;
    }
  });
  
  // 处理共同的行，进行单词级别的差异比较
  oldIndex = 0;
  newIndex = 0;
  
  for (let i = 0; i < Math.max(oldLines.length, newLines.length); i++) {
    const commonLineIndex = commonLines.findIndex(indices => 
      indices[0] === i || indices[1] === i
    );
    
    if (commonLineIndex !== -1) {
      // 这是一个共同的行，进行单词级别比较
      const [oldI, newI] = commonLines[commonLineIndex];
      if (oldLines[oldI] === newLines[newI]) {
        // 完全相同的行
        diffResults.push([{ value: oldLines[oldI] }]);
      } else {
        // 行内有差异，进行单词级别比较
        const wordDiff = Diff.diffWords(oldLines[oldI], newLines[newI]);
        diffResults.push(wordDiff);
      }
      
      if (oldI === i) oldIndex++;
      if (newI === i) newIndex++;
    } else if (i < oldLines.length && i >= newLines.length) {
      // 只存在于旧文本的行
      diffResults.push([{ value: oldLines[i], removed: true }]);
      oldIndex++;
    } else if (i >= oldLines.length && i < newLines.length) {
      // 只存在于新文本的行
      diffResults.push([{ value: newLines[i], added: true }]);
      newIndex++;
    } else if (oldIndex < oldLines.length && newIndex < newLines.length) {
      // 不匹配的行
      if (i === oldIndex && i !== newIndex) {
        diffResults.push([{ value: oldLines[oldIndex], removed: true }]);
        oldIndex++;
      } else if (i !== oldIndex && i === newIndex) {
        diffResults.push([{ value: newLines[newIndex], added: true }]);
        newIndex++;
      }
    }
  }
  
  return diffResults;
};

// --- 添加评分解析函数 ---
const parseEvaluationScores = (evaluationReport: any): { 
  scoreDetails: { category: string; score: number; maxScore: number; comment?: string }[],
  overallScore: number,
  guidelines?: string,
  suggestions?: string
} => {
  try {
    // 如果是字符串，尝试解析JSON
    let report: any;
    if (typeof evaluationReport === 'string') {
      try {
        report = JSON.parse(evaluationReport);
      } catch (e) {
        // 如果解析失败，尝试从文本中提取评分信息
        report = { 
          raw_text: evaluationReport,
          // 尝试从文本中提取总体评分
          overall_score: parseFloat(evaluationReport.match(/整体评分[：:]\s*(\d+(\.\d+)?)/i)?.[1] || "0")
        };
      }
    } else {
      report = evaluationReport;
    }
    
    let scoreDetails: { category: string; score: number; maxScore: number; comment?: string }[] = [];
    let overallScore = 0;
    let guidelines = '';
    let suggestions = '';
    
    // 尝试提取评分指南
    if (report.guidelines || report.evaluation_guidelines || report.criteria_explanation) {
      guidelines = report.guidelines || report.evaluation_guidelines || report.criteria_explanation;
    } else if (report.raw_text) {
      // 从原始文本中查找评分指南
      const guidelinesMatch = report.raw_text.match(/评分标准[：:]([\s\S]*?)(?=\n\n|$)/i);
      if (guidelinesMatch) {
        guidelines = guidelinesMatch[1].trim();
      }
    }
    
    // 尝试提取建议
    if (report.suggestions || report.recommendations || report.improvement_suggestions) {
      suggestions = report.suggestions || report.recommendations || report.improvement_suggestions;
    } else if (report.raw_text) {
      // 从原始文本中查找建议
      const suggestionsMatch = report.raw_text.match(/(?:建议|改进意见|提高建议)[：:]([\s\S]*?)(?=\n\n|$)/i);
      if (suggestionsMatch) {
        suggestions = suggestionsMatch[1].trim();
      }
    }
    
    // 尝试从不同的可能结构中提取评分
    if (report.scores) {
      // 场景1: 评分保存在scores字段中
      scoreDetails = Object.entries(report.scores).map(([category, value]: [string, any]) => ({
        category,
        score: typeof value === 'number' ? value : (value.score || 0),
        maxScore: value.max_score || 10,
        comment: value.comment || report.comments?.[category] || ''
      }));
      
      // 计算总分
      if (report.overall_score) {
        overallScore = report.overall_score;
      } else {
        const sum = scoreDetails.reduce((acc, item) => acc + item.score, 0);
        overallScore = scoreDetails.length > 0 ? sum / scoreDetails.length : 0;
      }
    } else if (report.criteria) {
      // 场景2: 评分保存在criteria字段中
      scoreDetails = report.criteria.map((item: any) => ({
        category: item.name || item.criterion || '',
        score: item.score || 0,
        maxScore: item.max_score || 10,
        comment: item.feedback || item.comment || ''
      }));
      
      overallScore = report.overall_score || 0;
    } else if (report.raw_text) {
      // 场景3: 尝试从原始文本中提取评分
      const scoreRegex = /(\w+)[评分分数]\s*[：:]\s*(\d+(\.\d+)?)\s*\/\s*(\d+)/gi;
      let match;
      
      while ((match = scoreRegex.exec(report.raw_text)) !== null) {
        scoreDetails.push({
          category: match[1].trim(),
          score: parseFloat(match[2]),
          maxScore: parseInt(match[4]) || 10,
          comment: ''
        });
      }
      
      // 尝试提取每个评分类别的评论
      scoreDetails.forEach(detail => {
        const commentRegex = new RegExp(`${detail.category}[评分分数][^]*?(评价|解释|原因|评论)[：:](.*?)(?=\n\n|$)`, 'i');
        const commentMatch = report.raw_text.match(commentRegex);
        if (commentMatch) {
          detail.comment = commentMatch[2].trim();
        }
      });
      
      if (scoreDetails.length > 0) {
        const sum = scoreDetails.reduce((acc, item) => acc + item.score, 0);
        overallScore = sum / scoreDetails.length;
      } else {
        overallScore = report.overall_score || 0;
      }
    } else {
      // 场景4: 尝试直接从对象中提取得分信息
      const scoreEntries = Object.entries(report).filter(([key, value]) => 
        !key.includes('comment') && !key.includes('feedback') && 
        !key.includes('explanation') && typeof value === 'number'
      );
      
      scoreDetails = scoreEntries.map(([category, value]) => ({
        category: category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        score: typeof value === 'number' ? value : 0,
        maxScore: 10,
        comment: report[`${category}_comment`] || report[`${category}_feedback`] || ''
      }));
      
      if (report.overall_score) {
        overallScore = report.overall_score;
      } else {
        const sum = scoreDetails.reduce((acc, item) => acc + item.score, 0);
        overallScore = scoreDetails.length > 0 ? sum / scoreDetails.length : 0;
      }
    }
    
    return { scoreDetails, overallScore, guidelines, suggestions };
  } catch (error) {
    console.error("解析评估报告时出错:", error);
    return { scoreDetails: [], overallScore: 0, guidelines: '', suggestions: '' };
  }
};

// 清理提示词，移除不必要的内容
const cleanPromptForCopy = (prompt: string): string => {
  const startMarker = "<<USER_COPY_PROMPT_START>>";
  const endMarker = "<<USER_COPY_PROMPT_END>>";
  
  // 检查是否包含标记
  if (prompt.includes(startMarker) && prompt.includes(endMarker)) {
    const startIndex = prompt.indexOf(startMarker) + startMarker.length;
    const endIndex = prompt.indexOf(endMarker);
    
    // 如果标记位置有效，提取标记之间的内容
    if (startIndex > -1 && endIndex > startIndex) {
      return prompt.substring(startIndex, endIndex).trim();
    }
  }
  
  return prompt.trim();
};

// 解析优化后的提示词，分离实际提示词和改进说明
const parseOptimizedPrompt = (fullPrompt: string): { promptContent: string; improvementNotes: string | null } => {
  const startMarker = "<<USER_COPY_PROMPT_START>>";
  const endMarker = "<<USER_COPY_PROMPT_END>>";
  const promptPrefix = "目标提示词：";
  const notesPrefix = "改进说明：";
  const markdownRegex = /```markdown|```/g;
  
  const result = {
    promptContent: "",
    improvementNotes: null as string | null
  };
  
  // 首先检查是否包含新的标记
  if (fullPrompt.includes(startMarker) && fullPrompt.includes(endMarker)) {
    const startIndex = fullPrompt.indexOf(startMarker) + startMarker.length;
    const endIndex = fullPrompt.indexOf(endMarker);
    
    // 如果标记位置有效，提取标记之间的内容
    if (startIndex > -1 && endIndex > startIndex) {
      result.promptContent = fullPrompt.substring(startIndex, endIndex).trim();
      
      // 尝试从标记外提取改进说明
      const afterEndMarker = fullPrompt.substring(endIndex + endMarker.length).trim();
      if (afterEndMarker && afterEndMarker.includes(notesPrefix)) {
        const notesIndex = afterEndMarker.indexOf(notesPrefix);
        result.improvementNotes = afterEndMarker.substring(notesIndex + notesPrefix.length).trim();
      }
      
      return result;
    }
  }
  
  // 如果没有找到新标记，使用原有逻辑
  if (fullPrompt.includes(promptPrefix)) {
    // 分行处理，跳过重复的"目标提示词："行和空行
    const lines = fullPrompt.split('\n');
    let contentStarted = false;
    let contentLines = [];
    let notesStarted = false;
    let notesLines = [];
    
    for (let line of lines) {
      const trimmedLine = line.trim();
      
      // 检查是否是改进说明行
      if (trimmedLine.includes(notesPrefix)) {
        notesStarted = true;
        continue; // 跳过这一行
      }
      
      // 收集改进说明内容
      if (notesStarted) {
        notesLines.push(line);
        continue;
      }
      
      // 跳过重复的前缀行和空行
      if (!contentStarted) {
        if (trimmedLine === "" || 
            trimmedLine === promptPrefix || 
            trimmedLine.includes(promptPrefix) || 
            trimmedLine === "**目标提示词：**" ||
            trimmedLine.includes("# 优化后的目标提示词")) {
          continue;
        }
        contentStarted = true;
      }
      
      // 收集实际内容行
      if (contentStarted) {
        contentLines.push(line);
      }
    }
    
    result.promptContent = contentLines.join('\n').trim();
    result.improvementNotes = notesLines.length > 0 ? notesLines.join('\n').trim() : null;
  } else if (fullPrompt.match(markdownRegex)) {
    // 如果包含markdown标记，从标记后找到第一个非空行开始提取
    const lines = fullPrompt.split('\n');
    let markdownLineIndex = -1;
    
    // 查找markdown标记行
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('```markdown') || lines[i] === '```') {
        markdownLineIndex = i;
        break;
      }
    }
    
    if (markdownLineIndex >= 0) {
      // 找到第一个非空内容行
      let contentStartIndex = markdownLineIndex + 1;
      while (contentStartIndex < lines.length && 
             (lines[contentStartIndex].trim() === "" || 
              lines[contentStartIndex].includes("# 优化") || 
              lines[contentStartIndex].includes("目标提示词"))) {
        contentStartIndex++;
      }
      
      if (contentStartIndex < lines.length) {
        // 从找到的内容行开始提取
        result.promptContent = lines.slice(contentStartIndex).join('\n').trim();
        
        // 寻找改进说明
        const notesIndex = result.promptContent.indexOf(notesPrefix);
        if (notesIndex > 0) {
          result.improvementNotes = result.promptContent.substring(notesIndex + notesPrefix.length).trim();
          result.promptContent = result.promptContent.substring(0, notesIndex).trim();
        }
      } else {
        // 如果没找到内容行，返回整个内容
        result.promptContent = fullPrompt.trim();
      }
    } else {
      // 如果格式不匹配，返回整个内容
      result.promptContent = fullPrompt.trim();
    }
  } else {
    // 如果不包含前缀和markdown标记，则整个内容作为提示词
    result.promptContent = fullPrompt.trim();
  }
  
  return result;
};

// 添加模板接口定义
interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  template: string;
  taskType: string;
}

// 修改任务类型定义添加下拉状态
interface TaskType {
  label: string;
  value: string;
  Icon: React.FC;
  isDropdownOpen?: boolean;
}

// 添加模板数据
const PROMPT_TEMPLATES: PromptTemplate[] = [
  // 研究类模板
  {
    id: "research_academic",
    name: "学术研究",
    description: "适用于学术论文、文献综述等学术研究",
    template: `角色：你是一位研究助手，具有丰富的学术知识和批判性思维能力。
任务：针对以下研究主题，提供深入分析和关键见解。
研究主题：{{主题}}
要求：
1. 提供主题的背景和重要性
2. 总结当前研究的主要观点和争议
3. 分析3-5个关键研究发现或理论
4. 指出研究中的方法论优缺点
5. 提出有价值的未来研究方向
格式：分段论述，使用学术语言，但避免过度技术性术语`,
    taskType: "深度研究"
  },
  {
    id: "research_market",
    name: "市场研究",
    description: "适用于市场分析、竞品调研等商业研究",
    template: `角色：你是一位市场分析专家。
任务：针对以下市场/产品进行详细分析。
分析对象：{{产品/市场}}
要求：
1. 市场规模和增长趋势分析
2. 目标客户群体画像和需求分析
3. 主要竞争对手分析（3-5家）：优势、劣势、差异化策略
4. SWOT分析（优势、劣势、机会、威胁）
5. 推荐的市场进入或扩展策略
格式：分段客观分析，提供数据支持的观点`,
    taskType: "深度研究"
  },
  
  // 图像生成类模板
  {
    id: "image_realistic",
    name: "写实风格",
    description: "生成高度写实的逼真图像",
    template: `创建一张高度写实的{{主题}}图像。
样式：超写实主义摄影风格
要素：
- 主体：{{具体描述主体}}
- 环境：{{环境描述}}
- 光照：{{光照效果描述}}
- 色调：{{色调倾向}}
- 视角：{{视角描述}}
- 氛围：{{氛围描述}}
细节要求：高分辨率，逼真细节，照片级质量，自然光影效果
不需要：明显AI生成痕迹，畸变，水印`,
    taskType: "图像生成"
  },
  {
    id: "image_cartoon",
    name: "卡通风格",
    description: "生成卡通、动漫风格的图像",
    template: `创建一张卡通风格的{{主题}}图像。
样式：{{具体卡通风格，如：迪士尼/日式动漫/像素艺术等}}
要素：
- 主角：{{主角描述}}
- 场景：{{场景描述}}
- 动作：{{动作描述}}
- 表情：{{表情描述}}
- 配色：{{色彩风格}}
细节要求：鲜明的轮廓线，夸张的比例，符合所选卡通风格的美学特征
额外要素：{{任何特殊效果或风格元素}}`,
    taskType: "图像生成"
  },
  
  // 代码生成类模板
  {
    id: "code_function",
    name: "功能函数",
    description: "生成特定功能的代码函数",
    template: `任务：创建一个{{编程语言}}函数，实现以下功能。
功能描述：{{详细功能描述}}
输入参数：
- {{参数1名称}}：{{类型}} - {{描述}}
- {{参数2名称}}：{{类型}} - {{描述}}
输出结果：{{返回值类型}} - {{返回值描述}}
代码要求：
1. 高效且优化的实现
2. 包含适当的错误处理
3. 添加清晰的注释
4. 遵循{{编程语言}}的最佳实践和风格指南
5. 提供使用示例`,
    taskType: "代码生成"
  },
  {
    id: "code_fullapp",
    name: "完整应用",
    description: "生成完整应用程序的代码结构",
    template: `任务：设计并实现一个{{应用类型}}应用。
应用名称：{{应用名称}}
功能需求：
1. {{功能1}}
2. {{功能2}}
3. {{功能3}}
技术栈：
- 前端：{{前端技术}}
- 后端：{{后端技术}}
- 数据库：{{数据库技术}}
- 其他依赖：{{其他技术依赖}}
代码结构要求：
1. 清晰的项目结构和文件组织
2. 使用设计模式和架构原则
3. 实现核心功能模块
4. 包含必要的注释和文档
5. 代码应具备可扩展性和可维护性`,
    taskType: "代码生成"
  },
  
  // 视频生成类模板
  {
    id: "video_explainer",
    name: "说明视频",
    description: "生成产品或概念的说明视频脚本",
    template: `任务：创建一个{{时长}}分钟的说明视频脚本，介绍{{主题}}。
目标受众：{{受众描述}}
视频风格：{{风格描述，如：专业/轻松/教育性等}}
脚本结构：
1. 开场白（10-15秒）：简短吸引人的介绍
2. 问题陈述（20-30秒）：说明该产品/概念解决什么问题
3. 解决方案介绍（主体部分）：
   - 关键特性1：{{特性1描述}}
   - 关键特性2：{{特性2描述}}
   - 关键特性3：{{特性3描述}}
4. 演示/案例（如适用）：展示实际应用场景
5. 好处总结：列出3-5个主要优势
6. 号召性行动：明确指导观众下一步行动
视觉元素建议：适当描述关键场景需要的视觉元素
配乐风格：建议背景音乐的风格`,
    taskType: "视频生成"
  },
  {
    id: "video_storyline",
    name: "故事情节",
    description: "创建视频故事情节和场景脚本",
    template: `任务：创建一个{{类型}}视频的故事板和分镜脚本。
视频时长：约{{时长}}分钟
故事主题：{{主题}}
目标受众：{{受众群体}}
视频风格：{{风格描述}}
情节结构：
1. 开场（设置和介绍）：
   - 场景描述：{{开场场景}}
   - 角色介绍：{{主要角色}}
   - 视觉氛围：{{氛围描述}}
2. 冲突/挑战展示：
   - 主要冲突：{{冲突描述}}
   - 情感转变：{{情感变化}}
3. 发展（主体部分）：
   - 关键场景1：{{场景1描述}}
   - 关键场景2：{{场景2描述}}
   - 关键场景3：{{场景3描述}}
4. 高潮：
   - 转折点：{{转折点描述}}
   - 视觉表现：{{关键视觉元素}}
5. 结局：
   - 解决方式：{{结局描述}}
   - 最终信息：{{最终要传达的信息}}
音乐和音效建议：{{音乐风格和关键音效}}
视觉风格指南：{{颜色方案、场景转换等}}`,
    taskType: "视频生成"
  },
  
  // 聊天机器人类模板
  {
    id: "chatbot_customer",
    name: "客服机器人",
    description: "设计客户服务聊天机器人的对话逻辑",
    template: `任务：设计一个{{行业}}客服聊天机器人的对话流程和回复模板。
机器人名称：{{名称}}
品牌语气：{{语气描述：专业/友好/正式等}}
主要功能：
1. 问候和身份识别
2. 常见问题解答
3. 问题分类和路由
4. 收集客户反馈
5. 升级至人工客服的条件
主要对话流程：
1. 欢迎语：{{欢迎语示例}}
2. 身份确认：{{确认方式}}
3. 问题分类提示：{{选项列表}}
常见问题及回复模板：
- 问题类别1：{{类别名称}}
  * Q: {{常见问题1}}
  * A: {{回答模板1}}
  * Q: {{常见问题2}}
  * A: {{回答模板2}}
- 问题类别2：{{类别名称}}
  * Q: {{常见问题1}}
  * A: {{回答模板1}}
升级条件：{{何时转人工客服}}
结束对话：{{结束语模板}}`,
    taskType: "聊天机器人"
  },
  {
    id: "chatbot_roleplay",
    name: "角色扮演",
    description: "创建特定角色或主题的聊天机器人",
    template: `任务：设计一个扮演{{角色/主题}}的聊天机器人。
角色设定：{{详细角色背景}}
性格特点：{{性格描述}}
知识领域：{{专业知识范围}}
语言风格：{{语言特点和风格}}
互动目标：{{与用户互动的主要目的}}
对话限制：
1. 不讨论的话题：{{禁止话题}}
2. 拒绝请求的回应方式：{{礼貌拒绝模板}}
主要对话示例：
- 问候：{{问候语示例}}
- 自我介绍：{{介绍模板}}
- 常见问题回应：
  * Q: {{问题示例1}}
  * A: {{回答示例1，体现角色特点}}
  * Q: {{问题示例2}}
  * A: {{回答示例2，体现角色特点}}
对话引导方式：{{如何引导对话继续}}
结束对话方式：{{如何自然结束对话}}`,
    taskType: "聊天机器人"
  },
  
  // 写作类模板
  {
    id: "writing_blog",
    name: "博客文章",
    description: "生成信息丰富的博客文章",
    template: `任务：撰写一篇关于{{主题}}的博客文章。
标题：{{主标题}}或生成引人注目的标题
目标读者：{{目标读者群体}}
文章风格：{{写作风格：专业/轻松/教育性等}}
文章长度：约{{字数}}字
文章结构：
1. 引言（吸引读者注意力，说明文章价值）
2. 主体部分：
   - 关键点1：{{要点1}}
   - 关键点2：{{要点2}}
   - 关键点3：{{要点3}}
   - 关键点4：{{要点4}}
3. 实用建议/操作步骤（如适用）
4. 结论与展望
SEO关键词：{{关键词1, 关键词2, 关键词3}}
内容要求：
- 包含实用信息和可操作的建议
- 提供相关数据或事实支持（如适用）
- 使用小标题、项目符号和短段落增强可读性
- 加入个人见解或独特观点
- 结尾包含号召性行动`,
    taskType: "内容写作"
  },
  {
    id: "writing_social",
    name: "社交媒体",
    description: "创建引人入胜的社交媒体内容",
    template: `任务：为{{平台名称}}创建关于{{主题}}的社交媒体内容。
内容类型：{{内容类型：帖子/故事/系列/活动等}}
目标受众：{{目标人群特征}}
品牌语气：{{语气：专业/幽默/励志/教育等}}
主要目标：{{营销目标：提高认知度/促进互动/引导转化等}}
内容元素：
1. 标题/开场句：{{引人注目的开场}}
2. 正文内容：简明扼要地传达关键信息
3. 号召性用语(CTA)：{{具体行动指示}}
4. 标签建议：{{相关标签列表}}
视觉元素建议：
- 图片类型：{{图片风格和内容建议}}
- 色彩主题：{{建议色调}}
- 文本叠加：{{文字叠加建议}}
发布时间建议：{{最佳发布时间}}
互动提示：鼓励评论/分享的问题或提示`,
    taskType: "内容写作"
  },
  {
    id: "writing_email",
    name: "电子邮件",
    description: "撰写专业的商务或营销邮件",
    template: `任务：创建一封关于{{主题}}的电子邮件。
邮件类型：{{类型：营销/通知/招聘/邀请等}}
目标读者：{{收件人描述}}
发件人：{{发件人身份/职位}}
主题行：{{邮件主题}}或提供吸引人的主题行建议
邮件结构：
1. 开场问候：{{适当的问候语}}
2. 引言段落：简明扼要地说明邮件目的
3. 主体内容：
   - 关键信息1：{{要点1}}
   - 关键信息2：{{要点2}}
   - 关键信息3：{{要点3}}
4. 号召性行动：明确指出收件人需要做什么
5. 结束语：{{适当的结束语}}
6. 签名：{{包含什么信息}}
语气和风格：{{正式/非正式/友好/专业等}}
设计考虑：
- 段落长度：保持简短清晰
- 强调重点：建议使用粗体或项目符号的内容
- 个性化元素：如何个性化邮件`,
    taskType: "内容写作"
  }
];

// 修改主题类型定义
type ThemeStyle = 'light' | 'dark' | 'cream';

// 添加JSON解析函数
const parseEvaluationJSON = (jsonData: any): {
  overallScore: number;
  criteria: Array<{
    name: string;
    score: number;
    maxScore: number;
    comment: string;
  }>;
  suggestions: string[];
  mainStrengths?: string;
  mainWeaknesses?: string;
  potentialRisks?: {
    level: string;
    description: string;
  };
} => {
  try {
    // 如果是字符串，尝试解析为JSON
    let data: any;
    if (typeof jsonData === 'string') {
      try {
        // 尝试清理字符串中可能导致JSON解析失败的内容
        let jsonString = jsonData.trim();
        
        // 查找JSON对象的开始和结束位置
        const startPos = jsonString.indexOf('{');
        const endPos = jsonString.lastIndexOf('}');
        
        if (startPos >= 0 && endPos > startPos) {
          jsonString = jsonString.substring(startPos, endPos + 1);
          data = JSON.parse(jsonString);
        } else {
          throw new Error("无法在字符串中找到有效的JSON对象");
        }
      } catch (e) {
        console.error("评估数据JSON解析失败:", e, "原始数据:", jsonData);
        
        // 返回一个空的结果
        return {
          overallScore: 0,
          criteria: [],
          suggestions: ["无法解析评估数据: " + (e instanceof Error ? e.message : String(e))]
        };
      }
    } else {
      data = jsonData;
    }
    
    console.log("解析的评估数据:", data); // 调试用
    
    let overallScore = 0;
    let criteria: Array<{name: string; score: number; maxScore: number; comment: string}> = [];
    let suggestions: string[] = [];
    let mainStrengths = '';
    let mainWeaknesses = '';
    let potentialRisks = {
      level: 'Low',
      description: ''
    };
    
    // 处理evaluation_summary部分
    if (data.evaluation_summary) {
      overallScore = data.evaluation_summary.overall_score || 0;
      mainStrengths = data.evaluation_summary.main_strengths || '';
      mainWeaknesses = data.evaluation_summary.main_weaknesses || '';
    }
    
    // 处理dimension_scores部分
    if (data.dimension_scores) {
      criteria = Object.entries(data.dimension_scores).map(([key, value]: [string, any]) => ({
        name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        score: value.score || 0,
        maxScore: 5, // 评分标准是1-5分
        comment: value.justification || ''
      }));
    }
    
    // 处理potential_risks部分
    if (data.potential_risks) {
      potentialRisks = {
        level: data.potential_risks.level || 'Low',
        description: data.potential_risks.description || ''
      };
    }
    
    // 处理suggestions_for_improvement部分
    if (data.suggestions_for_improvement) {
      if (Array.isArray(data.suggestions_for_improvement)) {
        suggestions = data.suggestions_for_improvement;
      } else if (typeof data.suggestions_for_improvement === 'string') {
        suggestions = [data.suggestions_for_improvement];
      }
    }
    
    // 计算总分（如果未提供）
    if (overallScore === 0 && criteria.length > 0) {
      const sum = criteria.reduce((acc, item) => acc + item.score, 0);
      overallScore = sum / criteria.length;
    }
    
    return { 
      overallScore, 
      criteria, 
      suggestions, 
      mainStrengths, 
      mainWeaknesses, 
      potentialRisks 
    };
  } catch (error) {
    console.error('解析评分JSON失败:', error);
    return {
      overallScore: 0,
      criteria: [],
      suggestions: ['无法解析评分数据: ' + (error instanceof Error ? error.message : String(error))]
    };
  }
};

// 添加评分卡片组件
const ScoreCard = ({ 
  evaluationData, 
  themeStyle
}: { 
  evaluationData: any,
  themeStyle: ThemeStyle
}) => {
  // 解析JSON评分数据
  const { overallScore, criteria, suggestions, mainStrengths, mainWeaknesses, potentialRisks } = parseEvaluationJSON(evaluationData);
  
  // 根据分数获取颜色
  const getScoreColor = (score: number): string => {
    if (score >= 4) return 'var(--color-success, #188038)';
    if (score >= 3) return 'var(--color-warning, #f9a825)';
    return 'var(--color-danger, #d93025)';
  };

  // 获取分数等级描述
  const getScoreLabel = (score: number): string => {
    if (score >= 4.5) return '优秀';
    if (score >= 4) return '良好';
    if (score >= 3) return '一般';
    if (score >= 2) return '需改进';
    return '不足';
  };
  
  // 获取总分的圆环背景色
  const getScoreRingColor = (score: number): string => {
    if (score >= 4) return '#e6f4ea'; // 淡绿色
    if (score >= 3) return '#fef7e0'; // 淡黄色
    return '#fce8e6'; // 淡红色
  };

  // 获取风险级别对应的颜色
  const getRiskLevelColor = (level: string): string => {
    switch(level.toLowerCase()) {
      case 'high': return 'var(--color-danger, #d93025)';
      case 'medium': return 'var(--color-warning, #f9a825)';
      default: return 'var(--color-success, #188038)';
    }
  };
  
  return (
    <div className={`score-card ${themeStyle}-theme`}>
      {/* 总体评分区 */}
      <div className="score-card-header">
        <div className="overall-score-container" style={{
          background: getScoreRingColor(overallScore),
          borderColor: getScoreColor(overallScore)
        }}>
          <div className="overall-score-circle">
            <span className="overall-score-value" style={{ color: getScoreColor(overallScore) }}>
              {overallScore.toFixed(1)}
            </span>
            <span className="overall-score-max">/5</span>
          </div>
          <div className="overall-score-label">
            <span className="score-rating">{getScoreLabel(overallScore)}</span>
            <span className="score-title">总体评分</span>
          </div>
        </div>
      </div>
      
      {/* 评分摘要区 */}
      {(mainStrengths || mainWeaknesses) && (
        <div className="score-summary">
          {mainStrengths && (
            <div className="score-strengths">
              <h4 className="summary-title"><span className="summary-icon">✓</span> 主要优点</h4>
              <p className="summary-text">{mainStrengths}</p>
            </div>
          )}
          {mainWeaknesses && (
            <div className="score-weaknesses">
              <h4 className="summary-title"><span className="summary-icon">!</span> 主要弱点</h4>
              <p className="summary-text">{mainWeaknesses}</p>
            </div>
          )}
        </div>
      )}
      
      {/* 分类评分列表 */}
      <div className="criteria-list">
        {criteria.length > 0 ? (
          criteria.map((item, index) => (
            <div className="criteria-item" key={index}>
              <div className="criteria-header">
                <h4 className="criteria-name">{item.name}</h4>
                <div className="criteria-score-container">
                  <span className="criteria-score" 
                    style={{ color: getScoreColor(item.score) }}>
                    {item.score.toFixed(1)}
                  </span>
                  <span className="criteria-max">/{item.maxScore}</span>
                </div>
              </div>
              
              <div className="criteria-bar-container">
                <div 
                  className="criteria-bar-fill"
                  style={{ 
                    width: `${(item.score / item.maxScore) * 100}%`,
                    backgroundColor: getScoreColor(item.score)
                  }}
                />
              </div>
              
              {item.comment && (
                <div className="criteria-comment">
                  <div className="comment-icon">💡</div>
                  <div className="comment-text">{item.comment}</div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="no-criteria-message">无评分数据</div>
        )}
      </div>
      
      {/* 潜在风险 */}
      {potentialRisks && potentialRisks.description && (
        <div className="risk-section">
          <h3 className="risk-title">
            <span className="risk-icon">⚠️</span>
            <span>潜在风险: </span>
            <span className="risk-level" style={{ color: getRiskLevelColor(potentialRisks.level) }}>
              {potentialRisks.level === 'High' ? '高' : potentialRisks.level === 'Medium' ? '中' : '低'}
            </span>
          </h3>
          <div className="risk-description">{potentialRisks.description}</div>
        </div>
      )}
      
      {/* 改进建议 */}
      {suggestions && suggestions.length > 0 && (
        <div className="suggestions-section">
          <h3 className="suggestions-title">
            <span className="suggestions-icon">✨</span>
            <span>改进建议</span>
          </h3>
          <div className="suggestions-content">
            {suggestions.length === 1 ? (
              <p>{suggestions[0]}</p>
            ) : (
              <ul className="suggestions-list">
                {suggestions.map((suggestion, index) => (
                  <li key={index} className="suggestion-item">{suggestion}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// 将SPECIFIC_TASK_TYPES从常量改为状态
function App() {
  // --- State Variables ---
  // 添加任务类型状态
  const [taskTypes, setTaskTypes] = useState<TaskType[]>(SPECIFIC_TASK_TYPES.map(type => ({...type, isDropdownOpen: false})));
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [showTemplateDrawer, setShowTemplateDrawer] = useState<boolean>(false);
  const [templateValues, setTemplateValues] = useState<{[key: string]: string}>({});
  const [rawRequest, setRawRequest] = useState<string>('');
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false); 
  const [error, setError] = useState<string | null>(null);   
  const [showIntro, setShowIntro] = useState<boolean>(true); 
  const [selectedTaskType, setSelectedTaskType] = useState<string | null>(SPECIFIC_TASK_TYPES[0].value); 
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [advancedMode, setAdvancedMode] = useState<boolean>(true);
  const [selfCorrection, setSelfCorrection] = useState<boolean>(true);
  const [recursionDepth, setRecursionDepth] = useState<number>(1);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [showSystemInfo, setShowSystemInfo] = useState<boolean>(false);
  const [allModels, setAllModels] = useState<ModelOption[]>([]);
  const [providers, setProviders] = useState<ProviderOption[]>([]);
  const [modelsByProvider, setModelsByProvider] = useState<{[key: string]: ModelOption[]}>({});
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("default");
  const [tooltipProvider, setTooltipProvider] = useState<string | null>(null);
  // @ts-ignore - 暂未使用，但保留以便未来功能扩展
  const [showResultSection, setShowResultSection] = useState<boolean>(false);
  // @ts-ignore - 暂未使用，但保留以便未来功能扩展
  const [selectedText, setSelectedText] = useState<string>('');
  const [showTermExplainer, setShowTermExplainer] = useState<boolean>(false);
  // 术语解释功能相关状态
  // @ts-ignore - 暂未使用的setter，保留以便未来功能扩展
  const [termToExplain, setTermToExplain] = useState<string>('');
  const [termExplanation, setTermExplanation] = useState<string>('');
  const [processedSteps, setProcessedSteps] = useState<ProcessedStep[]>([]);
  const [expandAllSteps, setExpandAllSteps] = useState<boolean>(false);
  // @ts-ignore - 暂未使用，但保留以便未来功能扩展
  const [showIntermediateSteps, setShowIntermediateSteps] = useState<boolean>(true);
  // @ts-ignore - 暂未使用，但保留以便未来功能扩展
  const [showFeedback, setShowFeedback] = useState<boolean>(false);
  const [feedbackRating, setFeedbackRating] = useState<number>(0);
  const [feedbackComment, setFeedbackComment] = useState<string>('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);
  const [showResultPage, setShowResultPage] = useState<boolean>(false);
  const [showStepsView, setShowStepsView] = useState<boolean>(false);
  const [initialPrompt, setInitialPrompt] = useState<string>('');
  const [comparisonMode, setComparisonMode] = useState<'side-by-side' | 'diff-highlight' | 'unified'>('side-by-side');
  const [showFeedbackPopup, setShowFeedbackPopup] = useState<boolean>(false);
  const [copiedToClipboard, setCopiedToClipboard] = useState<boolean>(false);
  const [selectedComparisonStep, setSelectedComparisonStep] = useState<number>(0);
  const [sourcePrompt, setSourcePrompt] = useState<string>('');
  const [targetPrompt, setTargetPrompt] = useState<string>('');
  const [themeStyle, setThemeStyle] = useState<ThemeStyle>('light');
  const [prompt, setPrompt] = useState<string>('');
  const [optimizedPrompt, setOptimizedPrompt] = useState<string>('');
  const [improvementNotes, setImprovementNotes] = useState<string | null>(null);
  const [isOptimized, setIsOptimized] = useState<boolean>(false);
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);

  // @ts-ignore - 暂未使用，但保留以便未来功能扩展
  const resultSectionRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const settingsPanelRef = useRef<HTMLDivElement>(null);

  // --- Helper Functions ---
  const getProviderDisplayName = useCallback((providerValue: string): string => {
    const provider = providers.find(p => p.value === providerValue);
    if (provider) return provider.name;
    if (providerValue) return providerValue.charAt(0).toUpperCase() + providerValue.slice(1);
    return "未知";
  }, [providers]);

  // --- Effects ---
  
  // 添加主题变化时的效果
  useEffect(() => {
    // 确保应用整体使用选定的主题
    document.body.className = `app-theme ${themeStyle}-theme`;
    
    // 存储主题选择到localStorage以便下次访问时恢复
    localStorage.setItem('thinkTwice-theme', themeStyle);
  }, [themeStyle]);
  
  // 初始化时从localStorage加载主题设置
  useEffect(() => {
    const savedTheme = localStorage.getItem('thinkTwice-theme') as ThemeStyle | null;
    if (savedTheme && ['light', 'dark', 'cream'].includes(savedTheme)) {
      setThemeStyle(savedTheme as ThemeStyle);
    } else {
      // 根据系统偏好设置默认主题
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setThemeStyle('dark');
      }
    }
  }, []);

  // 其他Effects保持不变
  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        const response = await fetch('/api/system/info');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data: SystemInfo = await response.json();
        setSystemInfo(data);
        if (data.available_models && data.available_models.length > 0) {
          setAllModels(data.available_models);
          const uniqueProvidersList: ProviderOption[] = [];
          const providerValuesSet = new Set<string>();
          const groupedModels: {[key: string]: ModelOption[]} = {};
          data.available_models.forEach(model => {
            if (!providerValuesSet.has(model.provider)) {
              providerValuesSet.add(model.provider);
              uniqueProvidersList.push({ name: model.provider.charAt(0).toUpperCase() + model.provider.slice(1), value: model.provider });
            }
            if (!groupedModels[model.provider]) groupedModels[model.provider] = [];
            groupedModels[model.provider].push(model);
          });
          setProviders(uniqueProvidersList);
          setModelsByProvider(groupedModels);
          const apiDefaultProvider = data.active_llm_provider || 'qwen';
          if (providerValuesSet.has(apiDefaultProvider)) setSelectedProvider(apiDefaultProvider);
          else if (uniqueProvidersList.length > 0) setSelectedProvider(uniqueProvidersList[0].value);
        } else {
           setProviders([]); setModelsByProvider({}); setSelectedProvider("");
        }
      } catch (err) { console.error('获取系统信息失败:', err); setError('无法加载模型信息，请检查API连接。'); }
    };
    fetchSystemInfo();
  }, []);
  
  useEffect(() => {
    if (selectedProvider && modelsByProvider[selectedProvider]) {
      const currentProviderModels = modelsByProvider[selectedProvider];
      const modelExistsInProvider = currentProviderModels.some(m => m.value === selectedModel);
      if (selectedModel !== "default" && !modelExistsInProvider) setSelectedModel("default");
    } else if (selectedProvider && !modelsByProvider[selectedProvider]) setSelectedModel("default");
  }, [selectedProvider, modelsByProvider, selectedModel]);

  useEffect(() => {
    const handleSelection = () => setSelectedText(window.getSelection()?.toString().trim() || '');
    document.addEventListener('mouseup', handleSelection); document.addEventListener('keyup', handleSelection);
    return () => { document.removeEventListener('mouseup', handleSelection); document.removeEventListener('keyup', handleSelection); };
  }, []);

  // 防止界面变白：确保generatedPrompt存在或加载完成后显示结果区域
  useEffect(() => {
    if (generatedPrompt || (!isLoading && error === null && !showIntro)) {
      setShowResultSection(true);
    }
  }, [generatedPrompt, isLoading, error, showIntro]);
  
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsPanelRef.current && !settingsPanelRef.current.contains(event.target as Node)) {
        const settingsButton = document.querySelector('.tool-button[title="设置"]');
        if (settingsButton && !settingsButton.contains(event.target as Node)) setShowSettings(false);
      }
    };
    if (showSettings) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showSettings]);

  // 添加一个新的Effect来处理提示词比较选择变化
  useEffect(() => {
    if (showStepsView && processedSteps.length > 0) {
      // 根据selectedComparisonStep确定源提示词和目标提示词
      if (selectedComparisonStep === 0) {
        // 初始提示词 vs 最终提示词
        setSourcePrompt(initialPrompt);
        setTargetPrompt(generatedPrompt);
      } else if (selectedComparisonStep > 0 && selectedComparisonStep <= processedSteps.length) {
        // 选择特定轮次比较
        const stepIndex = selectedComparisonStep - 1;
        setSourcePrompt(processedSteps[stepIndex].promptBeforeEvaluation);
        setTargetPrompt(processedSteps[stepIndex].promptAfterRefinement);
      }
    }
  }, [showStepsView, selectedComparisonStep, processedSteps, initialPrompt, generatedPrompt]);
  
  // 当选择新模板时，重置模板值
  useEffect(() => {
    if (selectedTemplate) {
      // 提取模板中的所有占位符
      const placeholders: string[] = [];
      const regex = /\{\{([^}]+)\}\}/g;
      let match;
      
      while ((match = regex.exec(selectedTemplate.template)) !== null) {
        // 避免重复添加相同的占位符
        if (!placeholders.includes(match[1])) {
          placeholders.push(match[1]);
        }
      }
      
      // 初始化模板值
      const initialValues: {[key: string]: string} = {};
      placeholders.forEach(placeholder => {
        initialValues[placeholder] = '';
      });
      
      setTemplateValues(initialValues);
    }
  }, [selectedTemplate]);

  // --- Event Handlers ---
  const handleSubmit = async () => {
    if (!prompt.trim()) return;
    
    setIsLoading(true);
      setError(null);
    setIsOptimized(false);
    setEvaluationData(null);
      
      abortControllerRef.current = new AbortController();
      
    try {
      let endpoint = '/api/generate-simple-p1';
      let requestData: any = {
        raw_request: prompt.trim(),
        task_type: selectedTaskType || DEFAULT_TASK_TYPE,
      };
      
      // 如果选择了特定的模型，添加到请求
      if (selectedProvider && selectedModel && selectedModel !== 'default') {
        requestData.model_info = {
        provider: selectedProvider,
          model: selectedModel
        };
      }
      
      // 高级模式 API
      if (advancedMode) {
        endpoint = '/api/generate-advanced-prompt';
        requestData = {
          ...requestData,
          enable_self_correction: selfCorrection,
          max_recursion_depth: recursionDepth
        };
      }
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
          body: JSON.stringify(requestData),
          signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP错误: ${response.status}` }));
        throw new Error(errorData.detail || '请求失败');
      }
      
      const data = await response.json();
      const resultText = advancedMode ? data.final_prompt : data.p1_prompt;
      
      // 解析优化后的提示词，分离内容和改进说明
      const { promptContent, improvementNotes: notes } = parseOptimizedPrompt(resultText);
      
      setOptimizedPrompt(promptContent);
      setImprovementNotes(notes);
      setIsOptimized(true);
      setInitialPrompt(prompt); // 保存初始提示词，用于比较
      
      // 如果是高级模式，并有评估报告
      if (advancedMode && data.evaluation_reports && data.evaluation_reports.length > 0) {
        // 如果有多个评估报告，处理步骤数据
        const processedSteps: ProcessedStep[] = [];
        
        if (data.refined_prompts && data.refined_prompts.length > 0) {
        for (let i = 0; i < data.evaluation_reports.length; i++) {
            try {
              const report = data.evaluation_reports[i];
              const scoreData = parseEvaluationScores(report);
              
              const promptBeforeEval = i === 0 ? data.initial_prompt : data.refined_prompts[i-1];
              const promptAfterRefinement = i < data.refined_prompts.length ? data.refined_prompts[i] : data.final_prompt;
              
              processedSteps.push({
            stepNumber: i + 1,
                promptBeforeEvaluation: promptBeforeEval,
                evaluationReport: report,
            promptAfterRefinement,
                isExpanded: i === 0, // 默认只展开第一步
                scoreDetails: scoreData.scoreDetails,
                overallScore: scoreData.overallScore,
                guidelines: scoreData.guidelines,
                suggestions: scoreData.suggestions
              });
            } catch (err) {
              console.error(`处理步骤 ${i+1} 时出错:`, err);
            }
          }
        }
        
        setProcessedSteps(processedSteps);
        
        // 解析最终评估报告
        try {
          const finalReport = data.evaluation_reports[data.evaluation_reports.length - 1];
          if (finalReport) {
            console.log("最终评估报告:", finalReport); // 调试用
            setEvaluationData(finalReport); // 直接设置原始评估数据
          }
        } catch (err) {
          console.error("解析评估报告失败:", err);
        }
      }
      
      // 切换到结果页面
      setShowResultPage(true);
      
    } catch (err: any) {
      // 如果是用户取消请求，不显示错误消息
      if (err.name === 'AbortError') {
        console.log('用户取消了请求');
        return;
      }
      
      setError(err.message || '出现错误，请稍后再试');
      console.error('提交请求出错:', err);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };
  
  const handleStop = () => { if (abortControllerRef.current) { abortControllerRef.current.abort(); setIsLoading(false); setError("用户已取消请求。"); } };
  const handleTaskTypeSelect = (taskValue: string) => setSelectedTaskType(selectedTaskType === taskValue ? null : taskValue);
  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => { if (event.key === 'Enter' && !event.shiftKey && !isLoading) { event.preventDefault(); handleSubmit(); } };
  
  // 处理术语解释功能 (暂未在UI中使用，但保留为未来可能的功能)
  // @ts-ignore - 未使用的函数，保留以待将来使用 
  const handleExplainTerm = async () => {
    if (!termToExplain || !generatedPrompt) { setError('请选择术语并确保已生成提示词'); return; }
    setIsLoading(true); setTermExplanation(''); setError(null);
    try {
      const modelInfo = selectedModel !== "default" && selectedProvider ? { model: selectedModel, provider: selectedProvider } : undefined;
      const response = await fetch('/api/explain-term', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ term_to_explain: termToExplain, context_prompt: generatedPrompt, model_info: modelInfo }) });
      if (!response.ok) { const errorData = await response.json().catch(() => ({ detail: `HTTP错误: ${response.status}` })); throw new Error(errorData.detail || `请求失败: ${response.status}`); }
      const data = await response.json();
      setTermExplanation(data.explanation || '未能获取解释'); setShowTermExplainer(true);
    } catch (err) { setError(err instanceof Error ? err.message : '解释术语时发生未知错误');
    } finally { setIsLoading(false); }
  };

  const handleSubmitFeedback = async () => {
    if (feedbackRating === 0) { setError('请选择评分'); return; }
    if (!generatedPrompt) { setError('没有可评价的提示词'); return; }
    setIsLoading(true); setError(null);
    try {
      const modelIdentifier = selectedModel !== "default" && selectedProvider && allModels.find(m => m.value === selectedModel && m.provider === selectedProvider)
        ? selectedModel
        : (systemInfo?.model_name || "default_model");
      const response = await fetch('/api/feedback/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt_id: Date.now().toString(), original_request: rawRequest, generated_prompt: generatedPrompt, rating: feedbackRating, comment: feedbackComment || undefined, model: modelIdentifier }) });
      if (!response.ok) { const errorData = await response.json(); throw new Error(errorData.detail || `请求失败: ${response.status}`); }
      setFeedbackSubmitted(true);
      setTimeout(() => { setShowFeedback(false); setFeedbackSubmitted(false); setFeedbackRating(0); setFeedbackComment(''); }, 2000);
    } catch (err) { setError(err instanceof Error ? err.message : '提交反馈时发生未知错误');
    } finally { setIsLoading(false); }
  };

  const toggleStepExpansion = (index: number) => {
    setProcessedSteps(prevSteps => prevSteps.map((step, i) => i === index ? { ...step, isExpanded: !step.isExpanded } : step));
  };
  const toggleAllStepsExpansion = () => {
    const nextState = !expandAllSteps;
    setExpandAllSteps(nextState);
    setProcessedSteps(prevSteps => prevSteps.map(step => ({ ...step, isExpanded: nextState })));
  };

  // 添加返回输入页面的函数
  const handleBackToInput = () => {
    setShowResultPage(false);
    setShowStepsView(false);
  };
  
  // 切换到自我校正与评估步骤视图
  const handleViewSteps = () => {
    setShowStepsView(true);
  };
  
  // 返回结果页面（从步骤视图）
  const handleBackToResult = () => {
    setShowStepsView(false);
  };
  
  // 复制到剪贴板并显示提示
  const handleCopyToClipboard = () => {
    if (optimizedPrompt) {
      navigator.clipboard.writeText(optimizedPrompt)
        .then(() => {
          setCopySuccess(true);
          setTimeout(() => setCopySuccess(false), 2000);
        })
        .catch(err => {
          console.error('复制失败:', err);
          setError('无法复制到剪贴板');
        });
    }
  };
  
  // 切换任务类型的下拉菜单
  const toggleTaskTypeDropdown = (index: number) => {
    setTaskTypes(prevTypes => 
      prevTypes.map((type, i) => 
        i === index 
          ? { ...type, isDropdownOpen: !type.isDropdownOpen } 
          : { ...type, isDropdownOpen: false }
      )
    );
  };
  
  // 选择模板
  const handleSelectTemplate = (template: PromptTemplate) => {
    setSelectedTemplate(template);
    
    // 选择对应的任务类型
    const taskTypeIndex = taskTypes.findIndex(type => type.value === template.taskType);
    if (taskTypeIndex !== -1) {
      // 直接设置选择的任务类型，不使用handleTaskTypeSelect，避免切换已选中状态
      setSelectedTaskType(template.taskType);
      
      // 关闭任务类型的下拉菜单
      setTaskTypes(prevTypes => 
        prevTypes.map(type => ({ ...type, isDropdownOpen: false }))
      );
    }
    
    setShowTemplateDrawer(true);
  };
  
  // 应用模板
  const applyTemplate = () => {
    if (!selectedTemplate) return;
    
    let processedTemplate = selectedTemplate.template;
    
    // 替换所有占位符
    Object.entries(templateValues).forEach(([placeholder, value]) => {
      const regex = new RegExp(`\\{\\{${placeholder}\\}\\}`, 'g');
      processedTemplate = processedTemplate.replace(regex, value || placeholder);
    });
    
    // 将处理后的模板设置为原始请求
    setRawRequest(processedTemplate);
    setShowTemplateDrawer(false);
  };
  
  // 更新模板值
  const handleTemplateValueChange = (placeholder: string, value: string) => {
    setTemplateValues(prev => ({
      ...prev,
      [placeholder]: value
    }));
  };

  // --- Render Functions ---
  const renderModelSelectionUI = () => ( <> <div className="settings-section"> <h4 className="settings-section-title">模型选择</h4> <div className="settings-row"> <label htmlFor="provider-select">提供商:</label> <select id="provider-select" value={selectedProvider} onChange={(e) => { setSelectedProvider(e.target.value); setSelectedModel("default"); setTooltipProvider(null); }} className="settings-select"> <option value="" disabled>选择提供商</option> {providers.map((p) => (<option key={p.value} value={p.value}>{p.name}</option>))} </select> </div> {selectedProvider && (<> <div className="settings-row selected-provider-display-row"> <span className="selected-provider-name" onMouseEnter={() => setTooltipProvider(selectedProvider)} onMouseLeave={() => setTooltipProvider(null)}> 已选: {getProviderDisplayName(selectedProvider)} <InfoIcon size={14} /> {tooltipProvider === selectedProvider && modelsByProvider[selectedProvider] && ( <div className="provider-models-tooltip"> <strong>{getProviderDisplayName(selectedProvider)} 模型:</strong> <ul> {modelsByProvider[selectedProvider].length > 0 ? modelsByProvider[selectedProvider].map((model) => (<li key={model.value}>{model.name}</li>)) : <li>无可用模型</li>} </ul> </div> )} </span> </div> <div className="settings-row"> <label htmlFor="model-select">具体模型:</label> <select id="model-select" value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} className="settings-select" disabled={!modelsByProvider[selectedProvider] || modelsByProvider[selectedProvider].length === 0}> <option value="default">默认 ({getProviderDisplayName(selectedProvider)})</option> {modelsByProvider[selectedProvider]?.map((model) => (<option key={model.value} value={model.value}>{model.name}</option>))} </select> </div> </>)} </div> </> );
  const renderAdvancedSettingsUI = () => ( <div className={`advanced-settings-content ${advancedMode ? 'open' : ''}`}> <ToggleSwitch id="self-correction-toggle" checked={selfCorrection} onChange={setSelfCorrection} label="启用自我校正" /> <div className="settings-row"> <label htmlFor="recursion-depth">最大递归深度:</label> <select id="recursion-depth" value={recursionDepth} onChange={(e) => setRecursionDepth(parseInt(e.target.value))} className="settings-select"> {[1, 2, 3].map(depth => (<option key={depth} value={depth}>{depth}</option>))} </select> </div> </div> );

  const renderIntermediateStep = (step: ProcessedStep, index: number) => (
    <div key={index} className={`correction-step ${step.isExpanded ? 'expanded' : ''}`}>
      <button className="step-header" onClick={() => toggleStepExpansion(index)}>
        <span className="step-number">第 {step.stepNumber} 轮优化</span>
        <span className="step-score">
          评分: <strong>{step.overallScore ? step.overallScore.toFixed(1) : 'N/A'}</strong>
        </span>
        <ChevronDownIcon className={`step-chevron ${step.isExpanded ? 'up' : ''}`} />
      </button>
      {step.isExpanded && (
        <div className="step-details">
          {step.overallScore !== undefined && (
            <div className="evaluation-score-card">
              {renderScoreCard(
                step.scoreDetails || [], 
                step.overallScore, 
                step.guidelines, 
                step.suggestions,
                step.evaluationReport // 传递评估报告
              )}
            </div>
          )}
          <div className="step-comparison-grid">
            <div className="step-content-block before">
              <div className="label">优化前 (P{step.stepNumber}):</div>
              <pre>{step.promptBeforeEvaluation || "N/A"}</pre>
            </div>
            <div className="step-content-block after">
              <div className="label">优化后 (P{step.stepNumber + 1}):</div>
              <pre>{step.promptAfterRefinement || "N/A"}</pre>
            </div>
          </div>
          {step.evaluationReport && (
            <div className="evaluation-report-step">
              <div className="label">AI评估报告 (E{step.stepNumber}):</div>
              <pre className="evaluation-content">
                {typeof step.evaluationReport === 'string' ? step.evaluationReport : JSON.stringify(step.evaluationReport, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // 渲染标签切换组件
  const renderTabSelector = () => (
    <div className="comparison-tabs">
      <button 
        className={`tab-button ${comparisonMode === 'side-by-side' ? 'active' : ''}`}
        onClick={() => setComparisonMode('side-by-side')}
      >
        并排对比
      </button>
      <button 
        className={`tab-button ${comparisonMode === 'diff-highlight' ? 'active' : ''}`}
        onClick={() => setComparisonMode('diff-highlight')}
      >
        差异高亮
      </button>
      <button 
        className={`tab-button ${comparisonMode === 'unified' ? 'active' : ''}`}
        onClick={() => setComparisonMode('unified')}
      >
        合并视图
      </button>
    </div>
  );
  
  // 渲染主题选择器
  const renderThemeSelector = () => {
    return (
      <div className="theme-selector">
        <label>主题风格：</label>
        <div className="theme-buttons">
          <button 
            className={`theme-button ${themeStyle === 'light' ? 'active' : ''}`}
            onClick={() => setThemeStyle('light')}
            title="亮色主题"
          >
            亮色
          </button>
          <button 
            className={`theme-button ${themeStyle === 'dark' ? 'active' : ''}`}
            onClick={() => setThemeStyle('dark')}
            title="暗色主题"
          >
            暗色
          </button>
          <button 
            className={`theme-button ${themeStyle === 'cream' ? 'active' : ''}`}
            onClick={() => setThemeStyle('cream')}
            title="米色主题"
          >
            米色
          </button>
        </div>
      </div>
    );
  };
  
  // 渲染评分卡片
  const renderScoreCard = (
    scoreDetails: { category: string; score: number; maxScore: number; comment?: string }[], 
    overallScore: number,
    // @ts-ignore - 下一行参数暂未使用，但保留以便未来功能扩展
    _guidelines?: string, 
    suggestions?: string,
    evaluationReport?: any
  ) => {
    // 如果有原始JSON评估报告，优先使用它
    if (evaluationReport) {
      return <ScoreCard evaluationData={evaluationReport} themeStyle={themeStyle} />;
    }
    
    // 向后兼容，使用旧结构
    // 将旧格式转换为新格式
    const transformedData = {
      overall_score: overallScore,
      criteria: scoreDetails.map(detail => ({
        name: detail.category,
        score: detail.score,
        max_score: detail.maxScore,
        comment: detail.comment || ''
      })),
      suggestions: suggestions || ''
    };
    
    return <ScoreCard evaluationData={transformedData} themeStyle={themeStyle} />;
  };
  
  // 渲染比较选择器
  const renderComparisonSelector = () => {
    const options = [
      { value: 0, label: "初始提示词 vs 最终提示词" },
      ...processedSteps.map((step) => ({
        value: step.stepNumber,
        label: `第 ${step.stepNumber} 轮优化前后`
      }))
    ];
    
    return (
      <div className="comparison-selector">
        <label htmlFor="comparison-select">选择比较轮次:</label>
        <div className="selector-wrapper">
          <select 
            id="comparison-select" 
            value={selectedComparisonStep}
            onChange={(e) => setSelectedComparisonStep(Number(e.target.value))}
            className="comparison-select"
          >
            {options.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <span className="select-arrow">▼</span>
        </div>
      </div>
    );
  };
  
  // 渲染差异高亮视图 - 更新使用源提示词和目标提示词
  const renderDiffHighlight = () => {
    // 使用diff库进行文本比较
    const diffResult = Diff.diffWords(sourcePrompt, targetPrompt);
    
    return (
      <div className="diff-highlight-view">
        <h4>差异高亮视图</h4>
        <pre className="highlighted-diff">
          {diffResult.map((part, index) => (
            <span 
              key={index}
              className={part.added ? 'added' : part.removed ? 'removed' : ''}
            >
              {part.value}
            </span>
          ))}
        </pre>
      </div>
    );
  };
  
  // 渲染合并视图 - 更新使用源提示词和目标提示词
  const renderUnifiedView = () => {
    // 使用行级别的比较进行合并视图
    const diffLines = compareTexts(sourcePrompt, targetPrompt);
    
    return (
      <div className="unified-view">
        <h4>合并视图</h4>
        <pre className="unified-diff">
          {diffLines.map((line, index) => (
            <div 
              key={index} 
              className={line[0].added ? 'line-added' : line[0].removed ? 'line-removed' : ''}
            >
              <span>
                {line[0].added ? '+ ' : line[0].removed ? '- ' : '  '}
              </span>
              <span>
                {line[0].value}
              </span>
            </div>
          ))}
        </pre>
      </div>
    );
  };
  
  // 渲染提示词对比视图 - 更新使用源提示词和目标提示词
  const renderPromptComparison = () => {
    switch(comparisonMode) {
      case 'side-by-side':
        return (
          <div className="side-by-side-comparison">
            <div className="comparison-column before">
              <h4>{selectedComparisonStep === 0 ? "初始提示词" : `优化前 (第 ${selectedComparisonStep} 轮)`}</h4>
              <pre>{sourcePrompt}</pre>
            </div>
            <div className="comparison-column after">
              <h4>{selectedComparisonStep === 0 ? "最终优化提示词" : `优化后 (第 ${selectedComparisonStep} 轮)`}</h4>
              <pre>{targetPrompt}</pre>
            </div>
          </div>
        );
      case 'diff-highlight':
        return renderDiffHighlight();
      case 'unified':
        return renderUnifiedView();
      default:
        return null;
    }
  };
  
  // 渲染模板列表
  const renderTemplateList = (taskType: string) => {
    const templates = PROMPT_TEMPLATES.filter(template => template.taskType === taskType);
    
    if (templates.length === 0) {
      return <div className="empty-templates">暂无可用模板</div>;
    }
  
  return (
      <div className="template-dropdown-menu">
        {templates.map(template => (
          <button 
            key={template.id} 
            className="template-item"
            onClick={() => handleSelectTemplate(template)}
          >
            <div className="template-item-header">
              <span className="template-name">{template.name}</span>
      </div>
            <div className="template-description">{template.description}</div>
          </button>
        ))}
      </div>
    );
  };
  
  // 渲染模板配置抽屉
  const renderTemplateDrawer = () => {
    if (!selectedTemplate) return null;
    
    // 提取模板中的所有占位符
    const placeholders: string[] = [];
    const regex = /\{\{([^}]+)\}\}/g;
    let match;
    // let templateText = selectedTemplate.template; // This variable is not used, can be removed
    
    while ((match = regex.exec(selectedTemplate.template)) !== null) {
      if (!placeholders.includes(match[1])) {
        placeholders.push(match[1]);
      }
    }
    
    return (
      <div className={`template-drawer ${showTemplateDrawer ? 'open' : ''}`}>
        <div className="template-drawer-header">
          <h3>配置模板: {selectedTemplate.name}</h3>
          <button 
            className="close-drawer-button" 
            onClick={() => setShowTemplateDrawer(false)}
            title="关闭"
          >
            <XIcon />
          </button>
          </div>
        
        <div className="template-drawer-content">
          <div className="template-description-full">
            <p>{selectedTemplate.description}</p>
          </div>
          
          <div className="template-placeholders">
            <h4>填写模板参数</h4>
            {placeholders.map(placeholder => (
              <div key={placeholder} className="placeholder-input">
                <label htmlFor={`placeholder-${placeholder}`}>{placeholder}:</label>
                <input
                  id={`placeholder-${placeholder}`}
                  type="text"
                  placeholder={`输入${placeholder}`}
                  value={templateValues[placeholder] || ''}
                  onChange={(e) => handleTemplateValueChange(placeholder, e.target.value)}
                />
              </div>
            ))}
          </div>
          
          <div className="template-preview">
            <h4>模板预览</h4>
            <pre className="template-preview-content">
              {selectedTemplate.template.replace(/\{\{([^}]+)\}\}/g, (_match, placeholder) => 
                templateValues[placeholder] ? templateValues[placeholder] : `{{${placeholder}}}`
              )}
            </pre>
          </div>
        </div>
        
        <div className="template-drawer-footer">
              <button
            className="cancel-button" 
            onClick={() => setShowTemplateDrawer(false)}
          >
            取消
          </button>
          <button 
            className="apply-template-button primary-button" 
            onClick={applyTemplate}
          >
            应用模板
          </button>
        </div>
      </div>
    );
  };
  
  // 修改任务类型选择器渲染
  const renderTaskTypeSelector = () => (
    <div className="task-type-selector">
      {taskTypes.map((task, index) => (
        <div key={task.value} className="task-button-container">
          <button
                className={`task-type-button ${selectedTaskType === task.value ? 'active' : ''}`}
            onClick={() => {
              handleTaskTypeSelect(task.value);
            }}
                title={task.label}
              >
                <task.Icon /> 
                <span className="task-button-label">{task.label}</span> 
            {PROMPT_TEMPLATES.some(template => template.taskType === task.value) && (
              <ChevronDownIcon 
                className={`dropdown-arrow ${task.isDropdownOpen ? 'up' : ''}`} 
                onClick={(e) => {
                  e.stopPropagation(); // 阻止事件冒泡，防止触发按钮点击事件
                  toggleTaskTypeDropdown(index);
                }}
              />
            )}
              </button>
          
          {task.isDropdownOpen && renderTemplateList(task.value)}
        </div>
            ))}
          </div>
  );
  
  // --- Main Render ---
  
  // 获取基于时间的欢迎语
  const getTimeBasedGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 6) {
      return "凌晨好";
    } else if (hour < 9) {
      return "早上好";
    } else if (hour < 12) {
      return "上午好";
    } else if (hour < 14) {
      return "中午好";
    } else if (hour < 18) {
      return "下午好";
    } else if (hour < 22) {
      return "晚上好";
    } else {
      return "夜深了";
    }
  };
  
  return (
    <div className={`app ${themeStyle}`}>
      {/* 页面头部 */}
      <header className="page-header">
        <div className="page-title">
          <img src={thinkTwiceLogo} alt="Think Twice Logo" className="page-title-logo" />
          <span className="page-title-text">Think Twice</span>
        </div>
        <div className="header-actions">
          <button 
            className="tool-button" 
            title="设置" 
            onClick={() => setShowSettings(!showSettings)}
          >
            <SettingsIcon />
          </button>
          <button 
            className="tool-button" 
            title="系统信息" 
            onClick={() => setShowSystemInfo(true)}
          >
            <InfoIcon />
          </button>
        </div>
      </header>
      
      <div ref={settingsPanelRef} className={`settings-panel ${showSettings ? 'open' : ''}`}> <div className="settings-panel-header"> <h3>应用设置</h3> <button className="close-panel-button" onClick={() => setShowSettings(false)} title="关闭设置"><XIcon/></button> </div> <div className="settings-panel-content"> <ToggleSwitch id="advanced-mode-toggle" checked={advancedMode} onChange={setAdvancedMode} label="高级模式" /> {advancedMode && renderAdvancedSettingsUI()} <hr className="settings-divider" /> {renderThemeSelector()} <hr className="settings-divider" /> {renderModelSelectionUI()} </div> </div>
      {showSystemInfo && systemInfo && ( 
        <div className="system-info-modal-overlay" onClick={() => setShowSystemInfo(false)}> 
          <div className="system-info-modal-content" onClick={(e) => e.stopPropagation()}> 
            <div className="system-info-modal-header"> 
              <h3>系统信息</h3> 
              <button onClick={() => setShowSystemInfo(false)} className="close-modal-button" title="关闭系统信息"><XIcon/></button> 
            </div> 
            <div className="info-grid"> 
              <div className="info-item">
                <strong>当前LLM提供商:</strong> 
                <span>{getProviderDisplayName(systemInfo.active_llm_provider)}</span>
              </div> 
              <div className="info-item">
                <strong>默认模型:</strong> 
                <span>{systemInfo.model_name}</span>
              </div> 
              <div className="info-item">
                <strong>API版本:</strong> 
                <span>{systemInfo.version}</span>
              </div> 
              <div className="info-item">
                <strong>可用提供商:</strong> 
                <span>{systemInfo.available_providers.map(getProviderDisplayName).join(', ')}</span>
              </div> 
              {systemInfo.structured_templates && (
                <div className="info-item">
                  <strong>可用模板:</strong> 
                  <span>{systemInfo.structured_templates.join(', ')}</span>
                </div>
              )} 
            </div> 
          </div> 
        </div> 
      )}
      {showIntro && (
        <div className="intro-modal-overlay" onClick={() => setShowIntro(false)}>
          <div className="intro-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="intro-modal-header">
              <h2>欢迎使用 Think Twice</h2>
              <button onClick={() => setShowIntro(false)} className="close-modal-button" title="关闭介绍"><XIcon/></button>
            </div>
            <div className="intro-modal-body">
              <p>这是一个旨在提升您思考深度与提问技巧的智能伙伴。它不仅能帮助您梳理和完善自身的想法，更能引导您向大型语言模型 (LLM) 提出更精准、更有效的问题，从而开启更高质量的AI对话与成果。</p>
              <div className="intro-example">
                <h4>它是如何工作的？看一个例子：</h4>
                <div className="example-grid">
                  <div className="example-before"> <h5>您的初步想法</h5> <pre>"帮我写个关于猫的科幻故事。"</pre> </div>
                  <div className="example-arrow">➡️</div>
                  <div className="example-after"> <h5>Think Twice 优化后</h5> <pre>角色：你是一位富有想象力的科幻小说家。{"\n"}任务：创作一个短篇科幻故事（约500字）。{"\n"}故事核心：一只普通的家猫意外获得了与宇宙深处一个古老AI交流的能力。{"\n"}关键情节：{"\n"}1. 猫如何发现这个能力。{"\n"}2. 与AI的首次交流，AI的目的。{"\n"}3. 猫因此面临的小冒险。{"\n"}4. 一个开放式结局。{"\n"}风格：略带幽默，充满好奇，适合年轻读者。{"\n"}输出：故事文本。</pre> </div>
                </div>
                <p className="example-explanation"> <strong>看！</strong> 优化后的提示通过设定角色、明确任务、提供关键情节和风格要求，能引导AI更精确地创作出您想要的故事。 </p>
              </div>
              <p className="intro-how-to-use"><strong>快速开始:</strong></p>
              <ul> <li>在下方选择一个任务场景。</li> <li>点击右上角设置图标 <SettingsIcon /> 可选择AI模型及高级功能。</li> <li>输入您的初步想法或问题。</li> <li>点击发送按钮 <CreativeSendIcon/> (或按Enter键)。</li> </ul>
            </div>
          </div>
        </div>
      )}
      {!showResultPage ? (
        /* 输入页面 - 确保输入框在页面中央 */
        <main className="input-page">
          <div className="centered-content">
            <h2 className="greeting-text">{getTimeBasedGreeting()}，欢迎使用 Think Twice</h2>
            
            <section className="input-area-container card-style"> 
              {renderTaskTypeSelector()} 
              
              <div className="prompt-input-container">
                <label htmlFor="prompt-input" className="sr-only">提示词输入</label>
                <textarea
                  id="prompt-input"
                  className="prompt-textarea"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="在此输入您的初步想法或问题..."
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                />
                
                <button 
                  className={`send-button ${isLoading ? 'loading' : ''}`} 
                  onClick={isLoading ? handleStop : handleSubmit} 
                  disabled={!isLoading && !prompt.trim()} 
                  title={isLoading ? "停止生成" : "优化提示"} 
                >
                  {isLoading ? <StopIcon /> : <CreativeSendIcon />} 
                </button>
              </div>
              
              <div className="input-area-footer"> 
                {advancedMode && <span className="mode-indicator-inline">高级模式已启用</span>} 
                {selectedProvider && ( 
                  <span className={`model-indicator-inline ${selectedProvider.toLowerCase()}`}> 
                    模型: {selectedModel === "default" ? `默认 (${getProviderDisplayName(selectedProvider)})` : allModels.find(m=>m.value === selectedModel && m.provider === selectedProvider)?.name || selectedModel} 
                  </span> 
                )} 
              </div> 
            </section>
            
            {error && <p className="error-message card-style">{error}</p>}
          </div>
      </main>
      ) : (
        /* 结果页面 - 显示优化后的提示词和操作按钮 */
        !showStepsView ? (
          <main className="result-page">
            <div className="result-header">
              <button className="back-button" onClick={handleBackToInput} title="返回">
                <ArrowLeftIcon />
                <span>返回</span>
              </button>
              
              <div className="result-actions">
                {advancedMode && processedSteps.length > 0 && (
                  <Button
                    variant="action"
                    icon={<CompareIcon />}
                    onClick={handleViewSteps}
                    title="查看自我校正与评估步骤"
                  >
                    <span>查看评估</span>
                  </Button>
                )}
                
                <Button
                  variant="action"
                  icon={<CopyIcon />}
                  onClick={handleCopyToClipboard}
                  title="复制到剪贴板"
                >
                  <span>复制提示词</span>
                  {copySuccess && <span className="copy-tooltip">已复制!</span>}
                </Button>
                
                <Button
                  variant="action"
                  icon={<PenIcon />}
                  onClick={() => setShowFeedbackPopup(true)}
                  title="提供反馈"
                >
                  <span>提供反馈</span>
                </Button>
              </div>
            </div>
            
            <div className="result-content">
              <h3>优化后的提示词:</h3>
              <pre className="final-prompt-display">{optimizedPrompt}</pre>
              
              {/* 改进说明区域 */}
              {improvementNotes && (
                <div className="prompt-improvement-notes-container">
                  <h4 className="prompt-improvement-notes-title">改进说明</h4>
                  <div className="prompt-improvement-notes">{improvementNotes}</div>
                </div>
              )}
              
              {/* 移除评估数据显示部分 */}
              
              {/* 展示反馈表单和其他内容... */}
              {showTermExplainer && termExplanation && (
                <div className="term-explainer card-style inset">
                  <div className="card-header">
                    <h4>"{termToExplain}" 的解释:</h4>
                    <button className="close-button" onClick={() => setShowTermExplainer(false)} title="关闭解释"><XIcon/></button>
                  </div>
                  <p>{termExplanation}</p>
                </div>
              )}
              
              {showFeedbackPopup && (
                <div className="feedback-popup-overlay">
                  <div className="feedback-popup">
                    <div className="popup-header">
                      <h4>您对生成的提示词满意吗？</h4>
                      <button className="close-button" onClick={() => setShowFeedbackPopup(false)} title="关闭反馈"><XIcon/></button>
                    </div>
                    
                    {feedbackSubmitted ? (
                      <div className="feedback-success">感谢您的反馈！</div>
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
                        <div className="popup-actions">
                          <button 
                            className="cancel-button" 
                            onClick={() => setShowFeedbackPopup(false)}
                          >
                            取消
                          </button>
                          <button 
                            className="submit-feedback-button primary-button" 
                            onClick={handleSubmitFeedback} 
                            disabled={feedbackRating === 0}
                          >
                            提交反馈
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </main>
        ) : (
          /* 步骤对比页面 */
          <main className="steps-page">
            <div className="result-header">
              <button className="back-button" onClick={handleBackToResult} title="返回结果页面">
                <ArrowLeftIcon />
                <span>返回结果</span>
              </button>
              
              <div className="view-actions">
                {renderTabSelector()}
              </div>
            </div>
            
            <div className="steps-content">
              {/* 添加比较选择器 */}
              {renderComparisonSelector()}
              
              {/* 提示词对比视图 */}
              <div className="prompt-comparison-view">
                {renderPromptComparison()}
              </div>
              
              {/* 评估步骤详情 */}
              <div className="intermediate-steps-container">
                <div className="intermediate-steps-header">
                  <h4>详细评估步骤:</h4>
                  <button className="tool-button toggle-all-steps-button" onClick={toggleAllStepsExpansion}>
                    {expandAllSteps ? <MinimizeIcon /> : <MaximizeIcon />}
                    {expandAllSteps ? "全部折叠" : "全部展开"}
                  </button>
                </div>
                {processedSteps.map((step, index) => renderIntermediateStep(step, index))}
              </div>
            </div>
          </main>
        )
      )}
      
      {/* 模板配置抽屉 */}
      {renderTemplateDrawer()}
      
      {/* 修改加载中遮罩，避免覆盖停止按钮 */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>正在生成优化提示...</p>
        </div>
      )}
    </div>
  );
}

export default App;




  