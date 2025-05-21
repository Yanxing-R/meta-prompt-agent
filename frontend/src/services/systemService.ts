import api from './api';
import type { ModelInfo } from './promptService';

export interface SystemInfo {
  active_llm_provider: string;
  model_name: string;
  available_providers: string[];
  version: string;
  structured_templates?: string[];
  available_models?: ModelOption[];
}

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

/**
 * 获取系统信息
 */
export async function getSystemInfo(): Promise<SystemInfo> {
  return api.fetchApi<SystemInfo>('/system/info');
}

/**
 * 获取当前使用的模型信息
 */
export async function getCurrentModelInfo(): Promise<{
  provider: string;
  model_name: string;
  timestamp: string;
}> {
  return api.fetchApi('/system/current-model');
}

/**
 * 将可用提供商列表转换为选项格式
 */
export function getProviderOptions(systemInfo: SystemInfo): ProviderOption[] {
  const providerDisplayMap: Record<string, string> = {
    'qwen': '通义千问',
    'gemini': 'Google Gemini',
    'ollama': 'Ollama (本地)',
    'openai': 'OpenAI',
    'anthropic': 'Anthropic'
  };
  
  return systemInfo.available_providers.map(provider => ({
    name: providerDisplayMap[provider] || provider,
    value: provider
  }));
}

/**
 * 根据提供商获取模型选项
 */
export function getModelsByProvider(
  systemInfo: SystemInfo
): Record<string, ModelOption[]> {
  if (!systemInfo.available_models) {
    return {};
  }
  
  const modelsByProvider: Record<string, ModelOption[]> = {};
  
  systemInfo.available_models.forEach(model => {
    if (!modelsByProvider[model.provider]) {
      modelsByProvider[model.provider] = [];
    }
    
    modelsByProvider[model.provider].push(model);
  });
  
  return modelsByProvider;
}

/**
 * 获取提供商的显示名称
 */
export function getProviderDisplayName(provider: string): string {
  const providerDisplayMap: Record<string, string> = {
    'qwen': '通义千问',
    'gemini': 'Google Gemini',
    'ollama': 'Ollama (本地)',
    'openai': 'OpenAI',
    'anthropic': 'Anthropic'
  };
  
  return providerDisplayMap[provider] || provider;
}

export default {
  getSystemInfo,
  getCurrentModelInfo,
  getProviderOptions,
  getModelsByProvider,
  getProviderDisplayName
}; 