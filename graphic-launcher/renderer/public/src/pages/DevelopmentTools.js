import React, { useState } from 'react';

const DevelopmentTools = () => {
  const [output, setOutput] = useState('');

  const startBackend = async () => {
    setOutput('正在啟動後端服務...\n');
    try {
      // This would typically involve starting multiple services
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

  const startFrontend = async () => {
    setOutput('正在啟動前端儀表板...\n');
    try {
      // This would typically involve starting the frontend dashboard
      const result = await window.electronAPI.runScript('apps/frontend-dashboard/start-dashboard.bat');
      if (result.success) {
        setOutput(prev => prev + result.stdout);
      } else {
        setOutput(prev => prev + `錯誤: ${result.error}\n${result.stderr}`);
      }
    } catch (error) {
      setOutput(prev => prev + `執行失敗: ${error.message}\n`);
    }
  };

  const startDesktopApp = async () => {
    setOutput('正在啟動桌面應用...\n');
    try {
      // This would typically involve starting the desktop app
      const result = await window.electronAPI.runScript('apps/desktop-app/start-desktop-app.bat');
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
    <div className="development-tools">
      <h1>開發工具</h1>
      <div className="controls">
        <button onClick={startBackend}>啟動後端服務</button>
        <button onClick={startFrontend}>啟動前端儀表板</button>
        <button onClick={startDesktopApp}>啟動桌面應用</button>
      </div>
      <div className="output">
        <h2>輸出結果</h2>
        <pre>{output}</pre>
      </div>
    </div>
  );
};

export default DevelopmentTools;