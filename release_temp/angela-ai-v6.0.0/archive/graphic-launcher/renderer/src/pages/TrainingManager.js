import React, { useState } from 'react';

const TrainingManager = () => {
  const [output, setOutput] = useState('');

  const setupTraining = async () => {
    setOutput('正在設置訓練環境...\n');
    try {
      const result = await window.electronAPI.runScript('tools/setup-training.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const startTraining = async () => {
    setOutput('正在啟動訓練...\n');
    try {
      const result = await window.electronAPI.runScript('tools/train-manager.bat', ['--start']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const stopTraining = async () => {
    setOutput('正在停止訓練...\n');
    try {
      const result = await window.electronAPI.runScript('tools/train-manager.bat', ['--stop']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const viewTrainingResults = async () => {
    setOutput('正在查看訓練結果...\n');
    try {
      const result = await window.electronAPI.runScript('tools/train-manager.bat', ['--results']);
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
    <div className="training-manager">
      <h1>訓練管理</h1>
      <div className="controls">
        <button onClick={setupTraining}>設置訓練環境</button>
        <button onClick={startTraining}>開始訓練</button>
        <button onClick={stopTraining}>停止訓練</button>
        <button onClick={viewTrainingResults}>查看訓練結果</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default TrainingManager;