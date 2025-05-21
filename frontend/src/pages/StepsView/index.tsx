import React, { useState } from 'react';
import Button from '../../components/common/Button';
import ComparisonView from '../../components/prompt/ComparisonView';
import EvaluationCard from '../../components/prompt/EvaluationCard';
import { ArrowLeftIcon } from '../../components/icons';
import './styles.css';

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

interface StepsViewProps {
  steps: ProcessedStep[];
  initialPrompt: string;
  finalPrompt: string;
  onBackToResult: () => void;
}

const StepsView: React.FC<StepsViewProps> = ({
  steps,
  initialPrompt,
  finalPrompt,
  onBackToResult
}) => {
  const [activeView, setActiveView] = useState<'diff' | 'unified' | 'evaluation'>('diff');
  const [expandedSteps, setExpandedSteps] = useState<number[]>([]);

  // 切换查看模式
  const handleViewChange = (view: 'diff' | 'unified' | 'evaluation') => {
    setActiveView(view);
  };

  // 切换步骤的展开/折叠状态
  const toggleStepExpansion = (stepIndex: number) => {
    if (expandedSteps.includes(stepIndex)) {
      setExpandedSteps(expandedSteps.filter(index => index !== stepIndex));
    } else {
      setExpandedSteps([...expandedSteps, stepIndex]);
    }
  };

  // 全部展开或折叠
  const toggleAllStepsExpansion = () => {
    if (expandedSteps.length === steps.length) {
      // 如果全部展开，则全部折叠
      setExpandedSteps([]);
    } else {
      // 否则全部展开
      setExpandedSteps(steps.map((_, index) => index));
    }
  };

  return (
    <div className="steps-view-page">
      <div className="steps-container">
        <div className="steps-header">
          <Button
            variant="outline"
            icon={<ArrowLeftIcon />}
            onClick={onBackToResult}
          >
            返回结果页
          </Button>
          <h2 className="steps-title">自我评估与改进步骤</h2>
        </div>
        
        <div className="view-selector">
          <button
            className={`view-tab ${activeView === 'diff' ? 'active' : ''}`}
            onClick={() => handleViewChange('diff')}
          >
            对比视图
          </button>
          <button
            className={`view-tab ${activeView === 'unified' ? 'active' : ''}`}
            onClick={() => handleViewChange('unified')}
          >
            统一视图
          </button>
          <button
            className={`view-tab ${activeView === 'evaluation' ? 'active' : ''}`}
            onClick={() => handleViewChange('evaluation')}
          >
            评估详情
          </button>
        </div>
        
        <div className="step-toggle-all">
          <button 
            className="toggle-all-button"
            onClick={toggleAllStepsExpansion}
          >
            {expandedSteps.length === steps.length ? '全部折叠' : '全部展开'}
          </button>
        </div>
        
        <div className="steps-content">
          {activeView === 'evaluation' ? (
            <div className="evaluation-container">
              {steps.map((step, index) => (
                <div className="step-evaluation" key={`eval-${index}`}>
                  <div className="step-evaluation-header">
                    <h3>步骤 {step.stepNumber} 评估</h3>
                  </div>
                  <EvaluationCard 
                    scoreDetails={step.scoreDetails || []}
                    overallScore={step.overallScore || 0}
                    suggestions={step.suggestions || ''}
                    evaluationReport={step.evaluationReport}
                  />
                </div>
              ))}
            </div>
          ) : (
            <div className="comparison-container">
              <ComparisonView 
                initialPrompt={initialPrompt}
                finalPrompt={finalPrompt}
                viewType={activeView}
              />
              
              {steps.map((step, index) => (
                <div 
                  className={`step-item ${expandedSteps.includes(index) ? 'expanded' : 'collapsed'}`}
                  key={`step-${index}`}
                >
                  <div 
                    className="step-header"
                    onClick={() => toggleStepExpansion(index)}
                  >
                    <span className="step-number">步骤 {step.stepNumber}</span>
                    <div className="step-toggle-icon">
                      {expandedSteps.includes(index) ? '−' : '+'}
                    </div>
                  </div>
                  
                  {expandedSteps.includes(index) && (
                    <div className="step-details">
                      <ComparisonView 
                        initialPrompt={step.promptBeforeEvaluation}
                        finalPrompt={step.promptAfterRefinement}
                        viewType={activeView}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StepsView; 