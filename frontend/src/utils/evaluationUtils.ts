import type { ParsedEvaluation, EvaluationScores } from '../types/prompt';

/**
 * 解析评估JSON数据
 */
export function parseEvaluationJSON(jsonData: any): ParsedEvaluation {
  if (!jsonData) {
    return {
      overallScore: 0,
      criteria: [],
      suggestions: [],
    };
  }
  
  try {
    // 确保数据是对象类型
    const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;
    
    // 初始化返回对象
    const result: ParsedEvaluation = {
      overallScore: data.overall_score || 0,
      criteria: [],
      suggestions: [],
    };
    
    // 处理评分标准
    if (data.criteria && Array.isArray(data.criteria)) {
      result.criteria = data.criteria.map((criterion: any) => ({
        name: criterion.name || criterion.criterion || '',
        score: criterion.score || 0,
        maxScore: criterion.max_score || 10,
        comment: criterion.comment || criterion.feedback || '',
      }));
    }
    
    // 处理建议
    if (data.suggestions) {
      if (Array.isArray(data.suggestions)) {
        result.suggestions = data.suggestions;
      } else if (typeof data.suggestions === 'string') {
        // 如果是字符串，可能是多行建议，按行分割
        result.suggestions = data.suggestions.split('\n').filter(Boolean);
      }
    }
    
    // 处理主要优点
    if (data.main_strengths || data.strengths) {
      result.mainStrengths = data.main_strengths || data.strengths;
    }
    
    // 处理主要弱点
    if (data.main_weaknesses || data.weaknesses) {
      result.mainWeaknesses = data.main_weaknesses || data.weaknesses;
    }
    
    // 处理潜在风险
    if (data.potential_risks || data.risks) {
      const risks = data.potential_risks || data.risks;
      if (typeof risks === 'object' && risks !== null) {
        result.potentialRisks = {
          level: risks.level || 'low',
          description: risks.description || '',
        };
      }
    }
    
    return result;
  } catch (error) {
    console.error('Error parsing evaluation JSON:', error);
    return {
      overallScore: 0,
      criteria: [],
      suggestions: [],
    };
  }
}

/**
 * 解析评估分数
 */
export const parseEvaluationScores = (evaluationReport: any): { 
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
    
    if (report.criteria && Array.isArray(report.criteria)) {
      // 结构化JSON格式
      scoreDetails = report.criteria.map((criterion: any) => ({
        category: criterion.name || criterion.category || '未命名标准',
        score: parseFloat(criterion.score) || 0,
        maxScore: criterion.maxScore || 10,
        comment: criterion.comment || criterion.description || ''
      }));
      
      overallScore = typeof report.overall_score === 'number' ? report.overall_score : 
                    (typeof report.overallScore === 'number' ? report.overallScore : 0);
      
      guidelines = report.guidelines || '';
      suggestions = Array.isArray(report.suggestions) 
                  ? report.suggestions.join('\n') 
                  : (report.suggestions || '');
    } else if (report.raw_text) {
      // 纯文本格式，尝试提取信息
      const text = report.raw_text;
      
      // 提取分数项
      const criteriaMatches = text.matchAll(/([^:\n]+)[:：]\s*(\d+(?:\.\d+)?)\s*\/\s*(\d+)(?:\s*-\s*([^\n]+))?/g);
      for (const match of criteriaMatches) {
        scoreDetails.push({
          category: match[1]?.trim() || '未命名标准',
          score: parseFloat(match[2]) || 0,
          maxScore: parseFloat(match[3]) || 10,
          comment: match[4]?.trim() || ''
        });
      }
      
      // 提取总分
      overallScore = report.overall_score || 0;
      
      // 提取建议
      const suggestionsMatch = text.match(/建议[：:]\s*([^#]+)/i);
      suggestions = suggestionsMatch ? suggestionsMatch[1].trim() : '';
    }
    
    return {
      scoreDetails,
      overallScore,
      guidelines,
      suggestions
    };
  } catch (e) {
    console.error('解析评估报告失败', e);
    return {
      scoreDetails: [],
      overallScore: 0,
      guidelines: '',
      suggestions: ''
    };
  }
};

/**
 * 解析优化后的提示词，提取正文和改进说明
 */
export const parseOptimizedPrompt = (fullPrompt: string): { promptContent: string; improvementNotes: string | null } => {
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

/**
 * 获取评分颜色
 */
export function getScoreColor(score: number): string {
  if (score >= 90) return '#4caf50';  // 优秀 - 绿色
  if (score >= 75) return '#8bc34a';  // 良好 - 浅绿色
  if (score >= 60) return '#ffc107';  // 中等 - 黄色
  if (score >= 40) return '#ff9800';  // 可接受 - 橙色
  return '#f44336';                   // 差 - 红色
}

/**
 * 获取评分标签
 */
export function getScoreLabel(score: number): string {
  if (score >= 90) return '优秀';
  if (score >= 75) return '良好';
  if (score >= 60) return '中等';
  if (score >= 40) return '可接受';
  return '需改进';
}

/**
 * 获取评分环的颜色
 */
export function getScoreRingColor(score: number): string {
  if (score >= 90) return 'var(--success-color)';
  if (score >= 75) return 'var(--success-light-color)';
  if (score >= 60) return 'var(--warning-color)';
  if (score >= 40) return 'var(--warning-dark-color)';
  return 'var(--error-color)';
}

/**
 * 获取风险等级颜色
 */
export function getRiskLevelColor(level: string): string {
  const lowerLevel = level.toLowerCase();
  if (lowerLevel.includes('low') || lowerLevel.includes('低')) return 'var(--success-light-color)';
  if (lowerLevel.includes('medium') || lowerLevel.includes('中')) return 'var(--warning-color)';
  if (lowerLevel.includes('high') || lowerLevel.includes('高')) return 'var(--error-color)';
  return 'var(--text-color)';
}

export default {
  parseEvaluationJSON,
  parseEvaluationScores,
  parseOptimizedPrompt,
  getScoreColor,
  getScoreLabel,
  getScoreRingColor,
  getRiskLevelColor
}; 