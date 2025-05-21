const API_BASE_URL = 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * 封装的fetch函数，添加了超时控制和错误处理
 */
export async function fetchApi<T = any>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { timeout = 30000, ...fetchOptions } = options;
  
  // 设置默认头信息
  const headers = new Headers(fetchOptions.headers);
  if (!headers.has('Content-Type') && !(fetchOptions.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  // 创建AbortController用于超时控制
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    // 检查HTTP状态
    if (!response.ok) {
      let errorMessage: string;
      
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || `HTTP错误: ${response.status}`;
      } catch {
        errorMessage = `HTTP错误: ${response.status}`;
      }
      
      throw new Error(errorMessage);
    }
    
    // 返回解析的JSON数据
    return await response.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('请求超时');
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * 创建可中止的API请求
 */
export function createAbortableFetch() {
  const controller = new AbortController();
  
  return {
    controller,
    abort: () => controller.abort(),
    fetchApi: <T = any>(endpoint: string, options: RequestInit = {}): Promise<T> => {
      return fetchApi<T>(endpoint, {
        ...options,
        signal: controller.signal,
      });
    }
  };
}

export default {
  fetchApi,
  createAbortableFetch
};

/**
 * API服务函数
 */

import { API_ENDPOINTS, ERROR_MESSAGES, REQUEST_TIMEOUT } from '../utils/constants';

/**
 * 带超时的fetch函数
 */
export const fetchWithTimeout = (url: string, options = {}, timeout = REQUEST_TIMEOUT): Promise<Response> => {
  return new Promise((resolve, reject) => {
    // 创建abort controller用于超时处理
    const controller = new AbortController();
    const signal = controller.signal;
    
    // 设置超时定时器
    const timeoutId = setTimeout(() => {
      controller.abort();
      reject(new Error(ERROR_MESSAGES.TIMEOUT));
    }, timeout);
    
    // 执行fetch请求
    fetch(url, { ...options, signal })
      .then(response => {
        clearTimeout(timeoutId);
        resolve(response);
      })
      .catch(error => {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
          reject(new Error(ERROR_MESSAGES.TIMEOUT));
        } else if (error.message === 'Network request failed' || !navigator.onLine) {
          reject(new Error(ERROR_MESSAGES.NETWORK));
        } else {
          reject(error);
        }
      });
  });
};

/**
 * 获取系统信息
 */
export const fetchSystemInfo = async () => {
  try {
    const response = await fetchWithTimeout(API_ENDPOINTS.SYSTEM_INFO);
    if (!response.ok) {
      throw new Error(ERROR_MESSAGES.SERVER);
    }
    return await response.json();
  } catch (error) {
    console.error('获取系统信息失败:', error);
    throw error;
  }
};

/**
 * 生成优化提示词
 */
export const generateAdvancedPrompt = async (
  promptText: string, 
  taskType: string, 
  provider: string, 
  model?: string, 
  selfCorrection = true, 
  recursionDepth = 2,
  abortSignal?: AbortSignal
) => {
  try {
    const requestData = {
      prompt: promptText,
      task_type: taskType,
      provider,
      model: model !== 'default' ? model : undefined,
      self_correction: selfCorrection,
      recursion_depth: recursionDepth
    };
    
    const response = await fetchWithTimeout(
      API_ENDPOINTS.GENERATE_ADVANCED_PROMPT,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
        signal: abortSignal
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || ERROR_MESSAGES.SERVER);
    }
    
    return await response.json();
  } catch (error) {
    console.error('生成提示词失败:', error);
    throw error;
  }
};

/**
 * 提交反馈
 */
export const submitFeedback = async (
  rating: number, 
  feedback: string, 
  initialPrompt: string, 
  optimizedPrompt: string, 
  taskType: string
) => {
  try {
    const response = await fetchWithTimeout(
      API_ENDPOINTS.FEEDBACK_SUBMIT,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating,
          feedback,
          initial_prompt: initialPrompt,
          optimized_prompt: optimizedPrompt,
          task_type: taskType
        })
      }
    );
    
    if (!response.ok) {
      throw new Error(ERROR_MESSAGES.SERVER);
    }
    
    return await response.json();
  } catch (error) {
    console.error('提交反馈失败:', error);
    throw error;
  }
}; 