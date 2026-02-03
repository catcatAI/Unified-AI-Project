import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import EnvironmentManager from './pages/EnvironmentManager';
import DevelopmentTools from './pages/DevelopmentTools';
import TestManager from './pages/TestManager';
import GitTools from './pages/GitTools';
import TrainingManager from './pages/TrainingManager';
import CliTools from './pages/CliTools';
import ModelManager from './pages/ModelManager';
import DataTools from './pages/DataTools';
import SystemTools from './pages/SystemTools';

const App = () => {
  const [activePage, setActivePage] = useState('dashboard');

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />;
      case 'environment':
        return <EnvironmentManager />;
      case 'development':
        return <DevelopmentTools />;
      case 'test':
        return <TestManager />;
      case 'git':
        return <GitTools />;
      case 'training':
        return <TrainingManager />;
      case 'cli':
        return <CliTools />;
      case 'model':
        return <ModelManager />;
      case 'data':
        return <DataTools />;
      case 'system':
        return <SystemTools />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
};

export default App;