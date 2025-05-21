import api from './api';

// 类型定义
export interface ModelInfo {
  model: string;
  provider: string;
}

export interface SimplePromptRequest {
  raw_request: string;
  task_type: string;
  model_info?: ModelInfo | null;
}

export interface SimplePromptResponse {
  p1_prompt: string;
  original_request: string;
  message?: string | null;
}

export interface AdvancedPromptRequest {
  raw_request: string;
  task_type: string;
  enable_self_correction: boolean;
  max_recursion_depth: number;
  template_name?: string | null;
  template_variables?: Record<string, any> | null;
  model_info?: ModelInfo | null;
}

export interface AdvancedPromptResponse {
  final_prompt: string;
  initial_prompt: string;
  refined_prompts?: string[];
  evaluation_reports?: any[];
  message?: string | null;
}

export interface ExplainTermRequest {
  term_to_explain: string;
  context_prompt: string;
  model_info?: ModelInfo | null;
}

export interface ExplanationResponse {
  explanation: string;
  term: string;
  context_snippet?: string | null;
  message?: string | null;
}

export interface FeedbackItem {
  prompt_id: string;
  original_request: string;
  generated_prompt: string;
  rating: number;
  comment?: string | null;
  model?: string | null;
}

export interface FeedbackResponse {
  success: boolean;
  message: string;
  feedback_id?: string | null;
}

export interface FeedbackListResponse {
  feedback_items: FeedbackItem[];
  total_count: number;
}

/**
 * 生成简单的优化提示词
 */
export async function generateSimplePrompt(
  rawRequest: string,
  taskType: string,
  modelInfo: ModelInfo | null = null
): Promise<SimplePromptResponse> {
  return api.fetchApi<SimplePromptResponse>('/generate-simple-p1', {
    method: 'POST',
    body: JSON.stringify({
      raw_request: rawRequest,
      task_type: taskType,
      model_info: modelInfo,
    }),
  });
}

/**
 * 生成高级优化提示词，支持自我校正和模板
 */
export async function generateAdvancedPrompt(
  rawRequest: string,
  taskType: string,
  enableSelfCorrection: boolean,
  maxRecursionDepth: number,
  templateName: string | null = null,
  templateVariables: Record<string, any> | null = null,
  modelInfo: ModelInfo | null = null
): Promise<AdvancedPromptResponse> {
  return api.fetchApi<AdvancedPromptResponse>('/generate-advanced-prompt', {
    method: 'POST',
    body: JSON.stringify({
      raw_request: rawRequest,
      task_type: taskType,
      enable_self_correction: enableSelfCorrection,
      max_recursion_depth: maxRecursionDepth,
      template_name: templateName,
      template_variables: templateVariables,
      model_info: modelInfo,
    }),
  });
}

/**
 * 解释提示词中的特定术语
 */
export async function explainTerm(
  termToExplain: string,
  contextPrompt: string,
  modelInfo: ModelInfo | null = null
): Promise<ExplanationResponse> {
  return api.fetchApi<ExplanationResponse>('/explain-term', {
    method: 'POST',
    body: JSON.stringify({
      term_to_explain: termToExplain,
      context_prompt: contextPrompt,
      model_info: modelInfo,
    }),
  });
}

/**
 * 提交用户反馈
 */
export async function submitFeedback(
  feedbackItem: FeedbackItem
): Promise<FeedbackResponse> {
  return api.fetchApi<FeedbackResponse>('/feedback/submit', {
    method: 'POST',
    body: JSON.stringify(feedbackItem),
  });
}

/**
 * 获取反馈列表
 */
export async function getFeedbackList(
  limit: number = 20,
  offset: number = 0,
  minRating?: number
): Promise<FeedbackListResponse> {
  let endpoint = `/feedback/list?limit=${limit}&offset=${offset}`;
  
  if (minRating !== undefined) {
    endpoint += `&min_rating=${minRating}`;
  }
  
  return api.fetchApi<FeedbackListResponse>(endpoint);
}

export default {
  generateSimplePrompt,
  generateAdvancedPrompt,
  explainTerm,
  submitFeedback,
  getFeedbackList,
}; 