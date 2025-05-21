import * as Diff from 'diff';
import type { DiffPart } from '../types/prompt';

/**
 * 将两段文本分解为行进行比较
 */
export function compareTexts(oldText: string, newText: string): DiffPart[][] {
  // 将文本按行分割
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  // 使用diff库进行行级别的差异比较
  const diffResult = Diff.diffArrays(oldLines, newLines);
  
  // 转换diff结果以便于渲染
  const lineByLineDiff: DiffPart[][] = [];
  
  diffResult.forEach(part => {
    part.value.forEach(line => {
      const diffLine: DiffPart[] = [{
        value: line,
        added: part.added,
        removed: part.removed
      }];
      lineByLineDiff.push(diffLine);
    });
  });
  
  return lineByLineDiff;
}

/**
 * 进行字符级别的差异比较
 */
export function compareTextDetails(oldText: string, newText: string): DiffPart[][] {
  // 将文本按行分割
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  // 对每行文本进行字符级别比较
  const result: DiffPart[][] = [];
  
  // 使用diff库进行行级别的差异比较，找出哪些行被添加/删除/修改
  const lineDiff = Diff.diffArrays(oldLines, newLines);
  
  // 处理完全添加或删除的行
  lineDiff.forEach(part => {
    if (part.added || part.removed) {
      part.value.forEach(line => {
        result.push([{
          value: line,
          added: part.added,
          removed: part.removed
        }]);
      });
    } else {
      // 对未改变的行，仍然作为一行添加
      part.value.forEach(line => {
        result.push([{
          value: line
        }]);
      });
    }
  });
  
  return result;
}

/**
 * 对两段文本做单词级别的差异比较
 */
export function compareWordsInTexts(oldText: string, newText: string): DiffPart[][] {
  // 将文本按行分割
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  // 使用diff-match-patch算法进行单词级别的比较
  const diffResults: DiffPart[][] = [];
  
  // 获取两个文本共同的行
  const lineDiff = Diff.diffArrays(oldLines, newLines);
  const commonLines: number[][] = []; // [oldIndex, newIndex]
  
  let oldIndex = 0;
  let newIndex = 0;
  
  lineDiff.forEach(part => {
    if (part.added) {
      // 添加的行，只存在于新文本
      newIndex += part.count || 0;
    } else if (part.removed) {
      // 删除的行，只存在于旧文本
      oldIndex += part.count || 0;
    } else {
      // 共同的行
      for (let i = 0; i < (part.count || 0); i++) {
        commonLines.push([oldIndex + i, newIndex + i]);
      }
      oldIndex += part.count || 0;
      newIndex += part.count || 0;
    }
  });
  
  // 处理共同的行，进行单词级别的差异比较
  oldIndex = 0;
  newIndex = 0;
  
  for (let i = 0; i < Math.max(oldLines.length, newLines.length); i++) {
    const commonLineIndex = commonLines.findIndex(indices => 
      indices[0] === i || indices[1] === i
    );
    
    if (commonLineIndex !== -1) {
      // 这是一个共同的行，进行单词级别比较
      const [oldI, newI] = commonLines[commonLineIndex];
      if (oldLines[oldI] === newLines[newI]) {
        // 完全相同的行
        diffResults.push([{ value: oldLines[oldI] }]);
      } else {
        // 行内有差异，进行单词级别比较
        const wordDiff = Diff.diffWords(oldLines[oldI], newLines[newI]);
        diffResults.push(wordDiff);
      }
      
      if (oldI === i) oldIndex++;
      if (newI === i) newIndex++;
    } else if (i < oldLines.length && i >= newLines.length) {
      // 只存在于旧文本的行
      diffResults.push([{ value: oldLines[i], removed: true }]);
      oldIndex++;
    } else if (i >= oldLines.length && i < newLines.length) {
      // 只存在于新文本的行
      diffResults.push([{ value: newLines[i], added: true }]);
      newIndex++;
    }
  }
  
  return diffResults;
}

/**
 * 清理提示词以便复制
 */
export function cleanPromptForCopy(prompt: string): string {
  // 移除最后一行的内容(如果它包含某些特定指示,如"现在请根据此提示生成内容"等)
  const lines = prompt.split('\n');
  
  // 检查最后一行是否包含一些常见的指示性文本
  const lastLine = lines[lines.length - 1].trim().toLowerCase();
  const indicativeTexts = [
    "现在请根据此提示生成内容",
    "✅",
    "请根据此提示生成内容",
    "* 现在请",
    "现在请你按照以上提示",
    "based on this prompt",
    "please generate content"
  ];
  
  if (indicativeTexts.some(text => lastLine.includes(text.toLowerCase()))) {
    lines.pop();
  }
  
  return lines.join('\n');
}

export default {
  compareTexts,
  compareTextDetails,
  compareWordsInTexts,
  cleanPromptForCopy
}; 