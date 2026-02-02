import React, { useState } from 'react';

const TestManager = () => {
  const [output, setOutput] = useState('');

  const runAllTests = async () => {
    setOutput('正在執行所有測試...\n');
    try {
      const result = await window.electronAPI.runScript('tools/run-tests.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const runUnitTests = async () => {
    setOutput('正在執行單元測試...\n');
    try {
      // This would typically involve running specific unit tests
      const result = await window.electronAPI.runScript('tools/run-tests.bat', ['--unit']);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const runIntegrationTests = async () => {
    setOutput('正在執行集成測試...\n');
    try {
      // This would typically involve running specific integration tests
      const result = await window.electronAPI.runScript('tools/run-tests.bat', ['--integration']);
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
    <div className="test-manager">
      <h1>測試管理</h1>
      <div className="controls">
        <button onClick={runAllTests}>執行所有測試</button>
        <button onClick={runUnitTests}>執行單元測試</button>
        <button onClick={runIntegrationTests}>執行集成測試</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default TestManager;