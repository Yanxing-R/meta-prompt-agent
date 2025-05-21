/**
 * 系统信息类型定义
 */
export interface ModelOption { 
  name: string; 
  value: string; 
  provider: string; 
  group: string; 
  id?: string; 
}

export interface ProviderOption { 
  name: string; 
  value: string; 
}

export interface SystemInfo { 
  active_llm_provider: string; 
  model_name: string; 
  available_providers: string[]; 
  version: string; 
  structured_templates?: string[]; 
  available_models?: ModelOption[]; 
}

/**
 * 处理过的评估步骤
 */
export interface ProcessedStep {
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

/**
 * API响应类型
 */
export interface SimplePromptResponse { 
  p1_prompt: string; 
}

export interface AdvancedPromptResponseAPI {
  final_prompt: string;
  initial_prompt: string;
  evaluation_reports?: any[];
  refined_prompts?: string[];
  message?: string;
} 