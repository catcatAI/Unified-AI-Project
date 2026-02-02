import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [systemInfo, setSystemInfo] = useState(null);
  const [environmentStatus, setEnvironmentStatus] = useState(null);

  useEffect(() => {
    // Fetch system information
    window.electronAPI.getSystemInfo().then((result) => {
      if (result.success) {
        setSystemInfo(result.data);
      }
    });

    // Check environment status
    window.electronAPI.checkEnvironment().then((result) => {
      if (result.success) {
        setEnvironmentStatus(result.data);
      }
    });
  }, []);

  const menuItems = [
    { id: 'environment', label: '環境管理', icon: '⚙️', description: '檢查和設置開發環境' },
    { id: 'development', label: '開發工具', icon: '💻', description: '啟動開發服務' },
    { id: 'test', label: '測試管理', icon: '✅', description: '執行測試套件' },
    { id: 'git', label: 'Git工具', icon: '🔄', description: 'Git狀態和清理' },
    { id: 'training', label: '訓練管理', icon: '🧠', description: 'AI模型訓練管理' },
    { id: 'cli', label: 'CLI工具', icon: '⌨️', description: '命令行工具訪問' },
    { id: 'model', label: '模型管理', icon: '📊', description: 'AI模型管理' },
    { id: 'data', label: '數據工具', icon: '📂', description: '數據分析和處理' },
    { id: 'system', label: '系統工具', icon: '🖥️', description: '系統信息和工具' }
  ];

  return (
    <div className="dashboard">
      <h1>Unified AI Project 圖形化啟動器</h1>
      <p>歡迎使用 Unified AI Project 圖形化啟動器。請選擇一個功能模塊開始使用。</p>

      <div className="system-info">
        <h2>系統信息</h2>
        {systemInfo ? (
          <div className="info-grid">
            <div className="info-item">
              <span className="label">操作系統:</span>
              <span className="value">{systemInfo.os}</span>
            </div>
            <div className="info-item">
              <span className="label">架構:</span>
              <span className="value">{systemInfo.arch}</span>
            </div>
            <div className="info-item">
              <span className="label">記憶體:</span>
              <span className="value">{systemInfo.memory}</span>
            </div>
          </div>
        ) : (
          <p>正在獲取系統信息...</p>
        )}
      </div>

      <div className="environment-status">
        <h2>環境狀態</h2>
        {environmentStatus ? (
          <div className="status-grid">
            <div className="status-item">
              <span className="label">Node.js:</span>
              <span className={`value ${environmentStatus.node.installed ? 'installed' : 'missing'}`}>
                {environmentStatus.node.installed ? `✓ ${environmentStatus.node.version}` : '✗ 未安裝'}
              </span>
            </div>
            <div className="status-item">
              <span className="label">Python:</span>
              <span className={`value ${environmentStatus.python.installed ? 'installed' : 'missing'}`}>
                {environmentStatus.python.installed ? `✓ ${environmentStatus.python.version}` : '✗ 未安裝'}
              </span>
            </div>
            <div className="status-item">
              <span className="label">pnpm:</span>
              <span className={`value ${environmentStatus.pnpm.installed ? 'installed' : 'missing'}`}>
                {environmentStatus.pnpm.installed ? `✓ ${environmentStatus.pnpm.version}` : '✗ 未安裝'}
              </span>
            </div>
          </div>
        ) : (
          <p>正在檢查環境狀態...</p>
        )}
      </div>

      <div className="quick-access">
        <h2>快速訪問</h2>
        <div className="cards">
          {menuItems.map((item) => (
            <div key={item.id} className="card">
              <div className="card-icon">{item.icon}</div>
              <h3>{item.label}</h3>
              <p>{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;