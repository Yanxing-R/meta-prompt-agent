import React from 'react';
import { CompareIcon } from '../../../components/icons';
import type { DiffPart } from '../../../types/prompt';
import Button from '../../../components/common/Button';
import './styles.css';

interface ComparisonViewProps {
  originalPrompt: string;
  optimizedPrompt: string;
  diffData: DiffPart[][];
  comparisonMode: 'none' | 'original_vs_final' | 'step_by_step';
  setComparisonMode: (mode: 'none' | 'original_vs_final' | 'step_by_step') => void;
  showDiff: boolean;
}

const ComparisonView: React.FC<ComparisonViewProps> = ({
  originalPrompt,
  optimizedPrompt,
  diffData,
  comparisonMode,
  setComparisonMode,
  showDiff
}) => {
  // 渲染对比选择器
  const renderComparisonSelector = () => (
    <div className="comparison-selector">
      <div className="comparison-selector-header">
        <CompareIcon />
        <span>对比视图</span>
      </div>
      
      <div className="comparison-buttons">
        <Button
          variant={comparisonMode === 'none' ? 'primary' : 'outline'}
          size="small"
          onClick={() => setComparisonMode('none')}
        >
          单视图
        </Button>
        
        <Button
          variant={comparisonMode === 'original_vs_final' ? 'primary' : 'outline'}
          size="small"
          onClick={() => setComparisonMode('original_vs_final')}
        >
          原始 vs 优化
        </Button>
        
        <Button
          variant={comparisonMode === 'step_by_step' ? 'primary' : 'outline'}
          size="small"
          onClick={() => setComparisonMode('step_by_step')}
        >
          逐步对比
        </Button>
      </div>
    </div>
  );
  
  // 渲染差异高亮
  const renderDiffHighlight = () => (
    <div className="diff-viewer">
      {diffData.map((diffLine, lineIndex) => (
        <div className="diff-line" key={lineIndex}>
          {diffLine.map((part, partIndex) => (
            <span
              key={partIndex}
              className={`diff-part ${part.added ? 'added' : ''} ${part.removed ? 'removed' : ''}`}
            >
              {part.value}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
  
  // 渲染统一视图
  const renderUnifiedView = () => (
    <div className="unified-view">
      <div className="unified-content">
        {showDiff ? renderDiffHighlight() : <pre>{optimizedPrompt}</pre>}
      </div>
    </div>
  );
  
  // 渲染并排对比视图
  const renderSideBySideView = () => (
    <div className="side-by-side-view">
      <div className="comparison-column">
        <div className="comparison-header">原始提示词</div>
        <div className="comparison-content">
          <pre>{originalPrompt}</pre>
        </div>
      </div>
      
      <div className="comparison-divider"></div>
      
      <div className="comparison-column">
        <div className="comparison-header">优化后的提示词</div>
        <div className="comparison-content">
          {showDiff ? renderDiffHighlight() : <pre>{optimizedPrompt}</pre>}
        </div>
      </div>
    </div>
  );
  
  // 主要渲染函数
  const renderPromptComparison = () => {
    if (comparisonMode === 'none') {
      return renderUnifiedView();
    } else if (comparisonMode === 'original_vs_final') {
      return renderSideBySideView();
    } else {
      // 'step_by_step' 模式 (假设逐步比较视图在另一个组件中实现)
      return (
        <div className="step-by-step-view">
          <div className="step-comparison-info">
            <p>逐步优化过程分析将在此显示</p>
          </div>
        </div>
      );
    }
  };
  
  return (
    <div className="comparison-view">
      {renderComparisonSelector()}
      {renderPromptComparison()}
    </div>
  );
};

export default ComparisonView; 