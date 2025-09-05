import React, { useState } from 'react';

const DataTools = () => {
  const [output, setOutput] = useState('');

  const analyzeData = async () => {
    setOutput('正在分析項目數據...\n');
    try {
      const result = await window.electronAPI.runCliCommand('data', ['analyze']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const runDataPipeline = async () => {
    setOutput('正在運行數據處理流水線...\n');
    try {
      const result = await window.electronAPI.runScript('tools/run_data_pipeline.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const viewDataStats = async () => {
    setOutput('正在查看數據統計信息...\n');
    try {
      const result = await window.electronAPI.runCliCommand('data', ['stats']);
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
    <div className="data-tools">
      <h1>數據工具</h1>
      <div className="controls">
        <button onClick={analyzeData}>數據分析</button>
        <button onClick={runDataPipeline}>運行數據流水線</button>
        <button onClick={viewDataStats}>查看數據統計</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default DataTools;