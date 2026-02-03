import React, { useState } from 'react';

const ModelManager = () => {
  const [output, setOutput] = useState('');

  const listModels = async () => {
    setOutput('正在列出所有模型...\n');
    try {
      const result = await window.electronAPI.runCliCommand('model', ['list']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const checkModelHealth = async () => {
    setOutput('正在檢查模型健康狀態...\n');
    try {
      const result = await window.electronAPI.runCliCommand('model', ['health']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const generateReport = async () => {
    setOutput('正在生成模型性能報告...\n');
    try {
      const result = await window.electronAPI.runCliCommand('model', ['report']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  return (
    <div className="model-manager">
      <h1>模型管理</h1>
      <div className="controls">
        <button onClick={listModels}>列出所有模型</button>
        <button onClick={checkModelHealth}>檢查模型健康</button>
        <button onClick={generateReport}>生成性能報告</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default ModelManager;