import React from 'react';
import type { ScoreCriterion, RiskLevel, ThemeStyle } from '../../../types/prompt';
import { getScoreColor, getScoreLabel, getScoreRingColor, getRiskLevelColor } from '../../../utils/evaluationUtils';
import './styles.css';

interface EvaluationCardProps {
  evaluationData: {
    overallScore: number;
    criteria: ScoreCriterion[];
    suggestions: string[];
    mainStrengths?: string;
    mainWeaknesses?: string;
    potentialRisks?: RiskLevel;
  };
  themeStyle: ThemeStyle;
}

const EvaluationCard: React.FC<EvaluationCardProps> = ({ 
  evaluationData, 
  themeStyle 
}) => {
  // 渲染得分环
  const renderScoreRing = () => {
    const { overallScore } = evaluationData;
    const scoreColor = getScoreRingColor(overallScore);
    
    return (
      <div className="score-ring-container">
        <svg width="120" height="120" viewBox="0 0 120 120">
          {/* 背景环 */}
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="var(--border-light-color)"
            strokeWidth="12"
          />
          
          {/* 得分环 */}
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke={scoreColor}
            strokeWidth="12"
            strokeDasharray={`${(overallScore / 100) * 339.3} 339.3`}
            strokeDashoffset="84.82"
            transform="rotate(-90 60 60)"
          />
          
          {/* 得分文本 */}
          <text
            x="60"
            y="50"
            textAnchor="middle"
            dominantBaseline="central"
            fontSize="28"
            fontWeight="bold"
            fill="var(--text-color)"
          >
            {overallScore}
          </text>
          
          {/* 满分标注 */}
          <text
            x="60"
            y="72"
            textAnchor="middle"
            dominantBaseline="central"
            fontSize="12"
            fill="var(--text-secondary-color)"
          >
            / 100
          </text>
          
          {/* 评级标签 */}
          <text
            x="60"
            y="90"
            textAnchor="middle"
            dominantBaseline="central"
            fontSize="14"
            fontWeight="bold"
            fill={scoreColor}
          >
            {getScoreLabel(overallScore)}
          </text>
        </svg>
      </div>
    );
  };
  
  // 渲染评分条目
  const renderScoreItem = (criterion: ScoreCriterion) => {
    const percentage = (criterion.score / criterion.maxScore) * 100;
    const barColor = getScoreColor(percentage);
    
    return (
      <div className="evaluation-score-item" key={criterion.name}>
        <div className="score-item-header">
          <span className="score-item-name">{criterion.name}</span>
          <span className="score-item-value">
            {criterion.score}/{criterion.maxScore}
          </span>
        </div>
        
        <div className="score-item-bar-container">
          <div 
            className="score-item-bar" 
            style={{ width: `${percentage}%`, backgroundColor: barColor }}
          ></div>
        </div>
        
        {criterion.comment && (
          <div className="score-item-comment">{criterion.comment}</div>
        )}
      </div>
    );
  };
  
  // 渲染建议列表
  const renderSuggestions = () => {
    const { suggestions } = evaluationData;
    
    if (!suggestions || suggestions.length === 0) {
      return null;
    }
    
    return (
      <div className="evaluation-suggestions">
        <h4>改进建议</h4>
        <ul>
          {suggestions.map((suggestion, index) => (
            <li key={index}>{suggestion}</li>
          ))}
        </ul>
      </div>
    );
  };
  
  // 渲染优缺点和风险
  const renderStrengthsAndWeaknesses = () => {
    const { mainStrengths, mainWeaknesses, potentialRisks } = evaluationData;
    
    return (
      <div className="strengths-weaknesses-section">
        {mainStrengths && (
          <div className="evaluation-strengths">
            <h4>主要优点</h4>
            <p>{mainStrengths}</p>
          </div>
        )}
        
        {mainWeaknesses && (
          <div className="evaluation-weaknesses">
            <h4>主要不足</h4>
            <p>{mainWeaknesses}</p>
          </div>
        )}
        
        {potentialRisks && (
          <div className="evaluation-risks">
            <h4>潜在风险</h4>
            <div 
              className="risk-level-indicator" 
              style={{ backgroundColor: getRiskLevelColor(potentialRisks.level) }}
            >
              {potentialRisks.level.toUpperCase()}
            </div>
            <p>{potentialRisks.description}</p>
          </div>
        )}
      </div>
    );
  };
  
  // 主渲染函数
  return (
    <div className={`evaluation-card ${themeStyle}`}>
      <div className="evaluation-card-header">
        <h3>提示词质量评估</h3>
        {renderScoreRing()}
      </div>
      
      <div className="evaluation-card-content">
        <div className="evaluation-score-list">
          {evaluationData.criteria.map(criterion => renderScoreItem(criterion))}
        </div>
        
        {renderStrengthsAndWeaknesses()}
        {renderSuggestions()}
      </div>
    </div>
  );
};

export default EvaluationCard; 