import React, { useState } from 'react';

const EnvironmentManager = () => {
  const [output, setOutput] = useState('');

  const runHealthCheck = async () => {
    setOutput('正在執行健康檢查...\n');
    try {
      const result = await window.electronAPI.runScript('tools/health-check.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const setupEnvironment = async () => {
    setOutput('正在設置環境...\n');
    try {
      const result = await window.electronAPI.runScript('tools/start-dev.bat');
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
    <div className="environment-manager">
      <h1>環境管理</h1>
      <div className="controls">
        <button onClick={runHealthCheck}>健康檢查</button>
        <button onClick={setupEnvironment}>設置環境</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default EnvironmentManager;