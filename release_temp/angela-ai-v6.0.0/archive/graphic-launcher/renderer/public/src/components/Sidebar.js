import React from 'react';

const Sidebar = ({ activePage, setActivePage }) => {
  const menuItems = [
    { id: 'dashboard', label: '主界面', icon: '🏠' },
    { id: 'environment', label: '環境管理', icon: '⚙️' },
    { id: 'development', label: '開發工具', icon: '💻' },
    { id: 'test', label: '測試管理', icon: '✅' },
    { id: 'git', label: 'Git工具', icon: '🔄' },
    { id: 'training', label: '訓練管理', icon: '🧠' },
    { id: 'cli', label: 'CLI工具', icon: '⌨️' },
    { id: 'model', label: '模型管理', icon: '📊' },
    { id: 'data', label: '數據工具', icon: '📂' },
    { id: 'system', label: '系統工具', icon: '🖥️' }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Unified AI Project</h2>
        <p>圖形化啟動器</p>
      </div>
      <nav className="sidebar-nav">
        <ul>
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                className={activePage === item.id ? 'active' : ''}
                onClick={() => setActivePage(item.id)}
              >
                <span className="icon">{item.icon}</span>
                <span className="label">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;