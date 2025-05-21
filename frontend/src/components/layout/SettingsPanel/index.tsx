import React, { useState } from 'react';
import { XIcon } from '../../../components/icons';
import ToggleSwitch from '../../../components/common/ToggleSwitch';
import Button from '../../../components/common/Button';
import type { ModelOption, ProviderOption } from '../../../services/systemService';
import { THEME_STYLES } from '../../../utils/constants';
import './styles.css';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  providers: ProviderOption[];
  selectedProvider: string;
  onProviderChange: (provider: string) => void;
  modelsByProvider: Record<string, ModelOption[]>;
  selectedModel: string;
  onModelChange: (model: string) => void;
  themeStyle: string;
  onThemeChange: (theme: string) => void;
  selfCorrection: boolean;
  onSelfCorrectionChange: (enabled: boolean) => void;
  recursionDepth: number;
  onRecursionDepthChange: (depth: number) => void;
  getProviderDisplayName: (provider: string) => string;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
  providers,
  selectedProvider,
  onProviderChange,
  modelsByProvider,
  selectedModel,
  onModelChange,
  themeStyle,
  onThemeChange,
  selfCorrection,
  onSelfCorrectionChange,
  recursionDepth,
  onRecursionDepthChange,
  getProviderDisplayName
}) => {
  const [tooltipProvider, setTooltipProvider] = useState<string | null>(null);
  
  if (!isOpen) return null;
  
  return (
    <div className="settings-panel-overlay">
      <div className="settings-panel">
        <div className="settings-header">
          <h2>设置</h2>
          <button 
            className="close-button" 
            onClick={onClose}
            aria-label="关闭"
          >
            <XIcon />
          </button>
        </div>
        
        <div className="settings-content">
          {/* 模型选择部分 */}
          <div className="settings-section">
            <h4 className="settings-section-title">模型选择</h4>
            <div className="settings-row">
              <label htmlFor="provider-select">提供商:</label>
              <select 
                id="provider-select" 
                value={selectedProvider} 
                onChange={(e) => {
                  onProviderChange(e.target.value);
                  setTooltipProvider(null);
                }}
                className="settings-select"
              >
                <option value="" disabled>选择提供商</option>
                {providers.map((p) => (
                  <option key={p.value} value={p.value}>{p.name}</option>
                ))}
              </select>
            </div>
            
            {selectedProvider && (
              <>
                <div className="settings-row selected-provider-display-row">
                  <span 
                    className="selected-provider-name"
                    onMouseEnter={() => setTooltipProvider(selectedProvider)}
                    onMouseLeave={() => setTooltipProvider(null)}
                  >
                    已选: {getProviderDisplayName(selectedProvider)}
                    {tooltipProvider === selectedProvider && modelsByProvider[selectedProvider] && (
                      <div className="provider-models-tooltip">
                        <strong>{getProviderDisplayName(selectedProvider)} 模型:</strong>
                        <ul>
                          {modelsByProvider[selectedProvider].length > 0 ? 
                            modelsByProvider[selectedProvider].map((model) => (
                              <li key={model.value}>{model.name}</li>
                            )) : 
                            <li>无可用模型</li>
                          }
                        </ul>
                      </div>
                    )}
                  </span>
                </div>
                
                <div className="settings-row">
                  <label htmlFor="model-select">具体模型:</label>
                  <select 
                    id="model-select" 
                    value={selectedModel} 
                    onChange={(e) => onModelChange(e.target.value)}
                    className="settings-select"
                    disabled={!modelsByProvider[selectedProvider] || modelsByProvider[selectedProvider].length === 0}
                  >
                    <option value="default">默认 ({getProviderDisplayName(selectedProvider)})</option>
                    {modelsByProvider[selectedProvider]?.map((model) => (
                      <option key={model.value} value={model.value}>{model.name}</option>
                    ))}
                  </select>
                </div>
              </>
            )}
          </div>
          
          {/* 主题设置部分 */}
          <div className="settings-section">
            <h4 className="settings-section-title">界面主题</h4>
            <div className="theme-selector">
              <span className="theme-selector-title">选择适合您的主题风格：</span>
              <div className="theme-buttons">
                <Button 
                  variant={themeStyle === THEME_STYLES.LIGHT ? 'primary' : 'outline'}
                  onClick={() => onThemeChange(THEME_STYLES.LIGHT)}
                  className={`theme-button ${themeStyle === THEME_STYLES.LIGHT ? 'active' : ''}`}
                >
                  默认
                </Button>
                <Button 
                  variant={themeStyle === THEME_STYLES.DARK ? 'primary' : 'outline'}
                  onClick={() => onThemeChange(THEME_STYLES.DARK)}
                  className={`theme-button ${themeStyle === THEME_STYLES.DARK ? 'active' : ''}`}
                >
                  深色
                </Button>
                <Button 
                  variant={themeStyle === THEME_STYLES.CREAM ? 'primary' : 'outline'}
                  onClick={() => onThemeChange(THEME_STYLES.CREAM)}
                  className={`theme-button ${themeStyle === THEME_STYLES.CREAM ? 'active' : ''}`}
                >
                  护眼
                </Button>
              </div>
            </div>
          </div>
          
          {/* 高级设置部分 */}
          <div className="settings-section">
            <h4 className="settings-section-title">高级设置</h4>
            <div className="advanced-settings-content">
              <ToggleSwitch 
                id="self-correction-toggle" 
                checked={selfCorrection} 
                onChange={onSelfCorrectionChange}
                label="启用自我校正"
              />
              
              <div className="settings-row">
                <label htmlFor="recursion-depth">最大递归深度:</label>
                <select 
                  id="recursion-depth" 
                  value={recursionDepth} 
                  onChange={(e) => onRecursionDepthChange(parseInt(e.target.value))}
                  className="settings-select"
                  disabled={!selfCorrection}
                >
                  {[1, 2, 3].map(depth => (
                    <option key={depth} value={depth}>{depth}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel; 