import React from "react";

export function Workflows() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Workflows</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Data Processing</h3>
          <p className="text-gray-600 mb-4">Automated data processing workflow</p>
          <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            Run Workflow
          </button>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Code Analysis</h3>
          <p className="text-gray-600 mb-4">Automated code review and analysis</p>
          <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            Run Workflow
          </button>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Report Generation</h3>
          <p className="text-gray-600 mb-4">Generate automated reports</p>
          <button className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600">
            Run Workflow
          </button>
        </div>
      </div>
    </div>
  );
}