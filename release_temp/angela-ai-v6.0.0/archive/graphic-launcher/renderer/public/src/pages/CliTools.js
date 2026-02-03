import React, { useState } from 'react';

const CliTools = () => {
  const [command, setCommand] = useState('');
  const [args, setArgs] = useState('');
  const [output, setOutput] = useState('');

  const runCommand = async () => {
    if (!command) {
      setOutput('請輸入命令\n');
      return;
    }

    setOutput(`正在執行命令: ${command} ${args}\n`);
    try {
      const argsArray = args.split(' ').filter(arg => arg.length > 0);
      const result = await window.electronAPI.runCliCommand(command, argsArray);
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const runHealthCheck = async () => {
    setCommand('health');
    setArgs('');
    setOutput('正在執行健康檢查...\n');
    try {
      const result = await window.electronAPI.runCliCommand('health');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const runSystemInfo = async () => {
    setCommand('system');
    setArgs('info');
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

  return (
    <div className="cli-tools">
      <h1>CLI工具</h1>
      <div className="command-input">
        <input
          type="text"
          placeholder="命令 (例如: health, system)"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
        />
        <input
          type="text"
          placeholder="參數 (例如: info, --verbose)"
          value={args}
          onChange={(e) => setArgs(e.target.value)}
        />
        <button onClick={runCommand}>執行</button>
      </div>
      <div className="quick-commands">
        <button onClick={runHealthCheck}>健康檢查</button>
        <button onClick={runSystemInfo}>系統信息</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default CliTools;