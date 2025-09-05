import React, { useState } from 'react';

const GitTools = () => {
  const [output, setOutput] = useState('');

  const checkGitStatus = async () => {
    setOutput('正在檢查Git狀態...\n');
    try {
      // This would typically involve running git commands
      const result = await window.electronAPI.runScript('tools/safe-git-cleanup.bat', ['--status']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const cleanGitRepo = async () => {
    setOutput('正在清理Git倉庫...\n');
    try {
      const result = await window.electronAPI.runScript('tools/safe-git-cleanup.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const viewErrorLogs = async () => {
    setOutput('正在查看錯誤日誌...\n');
    try {
      const result = await window.electronAPI.runScript('tools/view-error-logs.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const emergencyFix = async () => {
    setOutput('正在執行緊急Git修復...\n');
    try {
      const result = await window.electronAPI.runScript('tools/emergency-git-fix.bat');
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
    <div className="git-tools">
      <h1>Git工具</h1>
      <div className="controls">
        <button onClick={checkGitStatus}>檢查Git狀態</button>
        <button onClick={cleanGitRepo}>清理Git倉庫</button>
        <button onClick={viewErrorLogs}>查看錯誤日誌</button>
        <button onClick={emergencyFix}>緊急Git修復</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default GitTools;