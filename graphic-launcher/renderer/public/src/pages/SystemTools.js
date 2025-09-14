import React, { useState } from 'react';

const SystemTools = () => {
  const [output, setOutput] = useState('');

  const viewSystemInfo = async () => {
    setOutput('正在獲取系統信息...\n');
    try {
      const result = await window.electronAPI.runCliCommand('system', ['info']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const fixDependencies = async () => {
    setOutput('正在修復依賴問題...\n');
    try {
      const result = await window.electronAPI.runScript('tools/fix-dependencies.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const runSecurityCheck = async () => {
    setOutput('正在執行安全掃描...\n');
    try {
      const result = await window.electronAPI.runScript('tools/project-security-check.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const runBackup = async () => {
    setOutput('正在執行自動備份...\n');
    try {
      const result = await window.electronAPI.runScript('tools/automated-backup.bat');
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
    <div className="system-tools">
      <h1>系統工具</h1>
      <div className="controls">
        <button onClick={viewSystemInfo}>系統信息</button>
        <button onClick={fixDependencies}>修復依賴</button>
        <button onClick={runSecurityCheck}>安全掃描</button>
        <button onClick={runBackup}>自動備份</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default SystemTools;