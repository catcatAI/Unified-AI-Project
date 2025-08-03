import React from "react";

export function History() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">History</h1>
      
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Activities</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="font-medium">Chat Session</p>
              <p className="text-sm text-gray-600">2 hours ago</p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <p className="font-medium">Code Analysis</p>
              <p className="text-sm text-gray-600">5 hours ago</p>
            </div>
            <div className="border-l-4 border-purple-500 pl-4">
              <p className="font-medium">HSP Task</p>
              <p className="text-sm text-gray-600">1 day ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}