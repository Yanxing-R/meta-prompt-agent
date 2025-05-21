import type { TaskType } from '../types/prompt';
import { 
  ResearchIcon, 
  ImageIcon, 
  CodeIcon, 
  VideoIcon, 
  ChatbotIcon, 
  WritingIcon 
} from '../components/icons';

/**
 * 默认任务类型
 */
export const DEFAULT_TASK_TYPE = "通用/问答";

/**
 * 特定任务类型列表
 */
export const SPECIFIC_TASK_TYPES: TaskType[] = [
  { label: "研究", value: "深度研究", Icon: ResearchIcon },
  { label: "图像", value: "图像生成", Icon: ImageIcon },
  { label: "代码", value: "代码生成", Icon: CodeIcon },
  { label: "视频", value: "视频生成", Icon: VideoIcon },
  { label: "聊天", value: "聊天机器人", Icon: ChatbotIcon },
  { label: "写作", value: "内容写作", Icon: WritingIcon },
];

/**
 * 主题样式
 */
export const THEME_STYLES = {
  LIGHT: 'light',
  DARK: 'dark',
  CREAM: 'cream'
};

/**
 * 视图模式
 */
export const VIEW_MODES = {
  INPUT: 'input',
  RESULT: 'result',
  STEPS: 'steps'
};

/**
 * 比较模式
 */
export const COMPARE_MODES = {
  NONE: 'none',
  ORIGINAL_VS_FINAL: 'original_vs_final',
  STEP_BY_STEP: 'step_by_step'
};

/**
 * 本地存储键
 */
export const STORAGE_KEYS = {
  THEME: 'think-twice-theme',
  PROVIDER: 'think-twice-provider',
  MODEL: 'think-twice-model',
  SELF_CORRECTION: 'think-twice-self-correction',
  RECURSION_DEPTH: 'think-twice-recursion-depth'
};

/**
 * API端点
 */
export const API_ENDPOINTS = {
  SYSTEM_INFO: '/api/system/info',
  CURRENT_MODEL: '/api/system/current-model',
  GENERATE_SIMPLE_P1: '/api/generate-simple-p1',
  GENERATE_ADVANCED_PROMPT: '/api/generate-advanced-prompt',
  EXPLAIN_TERM: '/api/explain-term',
  FEEDBACK_SUBMIT: '/api/feedback/submit',
  FEEDBACK_LIST: '/api/feedback/list'
};

/**
 * 错误消息
 */
export const ERROR_MESSAGES = {
  DEFAULT: '发生了错误，请重试。',
  NETWORK: '网络连接错误，请检查您的互联网连接。',
  SERVER: '服务器错误，请稍后重试。',
  TIMEOUT: '请求超时，请检查您的网络连接或稍后重试。',
  MODEL_UNAVAILABLE: '所选模型当前不可用，请更换其他模型或稍后重试。',
  EMPTY_REQUEST: '请输入您的请求内容。'
};

// API URL
export const API_BASE_URL = 'http://localhost:8000'; // 本地开发服务器地址

// 输出标记
export const PROMPT_START_MARKER = "<<USER_COPY_PROMPT_START>>";
export const PROMPT_END_MARKER = "<<USER_COPY_PROMPT_END>>";

// 请求超时时间（毫秒）
export const REQUEST_TIMEOUT = 60000; // 60秒

export default {
  DEFAULT_TASK_TYPE,
  SPECIFIC_TASK_TYPES,
  THEME_STYLES,
  VIEW_MODES,
  COMPARE_MODES,
  STORAGE_KEYS,
  API_ENDPOINTS,
  ERROR_MESSAGES,
  API_BASE_URL,
  PROMPT_START_MARKER,
  PROMPT_END_MARKER,
  REQUEST_TIMEOUT
}; 