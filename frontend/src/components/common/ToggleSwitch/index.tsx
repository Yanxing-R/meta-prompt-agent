import React from 'react';
import './styles.css';

interface ToggleSwitchProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  disabled?: boolean;
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  id,
  checked,
  onChange,
  label,
  disabled = false
}) => {
  return (
    <div className="toggle-switch-container">
      <label htmlFor={id} className="toggle-switch-label">{label}</label>
      <label className="toggle-switch">
        <input
          type="checkbox"
          id={id}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
        />
        <span className="slider round"></span>
      </label>
    </div>
  );
};

export default ToggleSwitch; 