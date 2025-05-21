/**
 * 提示词相关类型定义
 */

/**
 * 任务类型定义
 */
export interface TaskType {
  label: string;
  value: string;
  Icon: React.FC;
  isDropdownOpen?: boolean;
}

/**
 * 提示词模板定义
 */
export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  template: string;
  taskType: string;
  placeholders?: string[];
}

/**
 * 提示词处理步骤
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
 * 差异比较部分
 */
export interface DiffPart {
  value: string;
  added?: boolean;
  removed?: boolean;
}

/**
 * 主题样式类型
 */
export type ThemeStyle = 'light' | 'dark' | 'cream';

/**
 * 评估报告中的评分标准
 */
export interface ScoreCriterion {
  name: string;
  score: number;
  maxScore: number;
  comment: string;
}

/**
 * 评估报告中的风险等级
 */
export interface RiskLevel {
  level: string;
  description: string;
}

/**
 * 解析后的评估报告
 */
export interface ParsedEvaluation {
  overallScore: number;
  criteria: ScoreCriterion[];
  suggestions: string[];
  mainStrengths?: string;
  mainWeaknesses?: string;
  potentialRisks?: RiskLevel;
}

/**
 * 评估分数详情
 */
export interface EvaluationScores {
  scoreDetails: {
    category: string;
    score: number;
    maxScore: number;
    comment?: string;
  }[];
  overallScore: number;
  guidelines?: string;
  suggestions?: string;
} 