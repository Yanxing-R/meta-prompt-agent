import React from 'react';
import { useNavigate } from 'react-router-dom';
import './styles.css';
import thinkTwiceLogo from '../../../assets/think-twice-logo.png';
import { SettingsIcon } from '../../icons';

interface HeaderProps {
  onSettingsClick: () => void;
  themeStyle: 'light' | 'dark' | 'cream';
  setThemeStyle: (theme: 'light' | 'dark' | 'cream') => void;
}

const Header: React.FC<HeaderProps> = ({ onSettingsClick, themeStyle, setThemeStyle }) => {
  const navigate = useNavigate();
  
  // 返回首页
  const handleLogoClick = () => {
    navigate('/');
  };
  
  // 切换主题
  const handleThemeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setThemeStyle(e.target.value as 'light' | 'dark' | 'cream');
  };
  
  return (
    <header className="app-header">
      <div className="header-logo" onClick={handleLogoClick}>
        <img src={thinkTwiceLogo} alt="Think Twice Logo" className="logo-image" />
        <span className="logo-text">Think Twice</span>
      </div>
      
      <div className="header-right">
        <div className="theme-selector">
          <label htmlFor="theme-select" className="visually-hidden">选择主题</label>
          <select 
            id="theme-select"
            value={themeStyle} 
            onChange={handleThemeChange}
            className="theme-select"
            aria-label="选择主题"
          >
            <option value="light">浅色主题</option>
            <option value="dark">深色主题</option>
            <option value="cream">护眼模式</option>
          </select>
        </div>
        
        <button className="settings-button" onClick={onSettingsClick} title="设置">
          <SettingsIcon />
        </button>
      </div>
    </header>
  );
};

export default Header; 