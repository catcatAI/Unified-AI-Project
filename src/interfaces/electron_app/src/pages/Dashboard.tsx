import React from "react";

const Dashboard = () => {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <div className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
        <h2 className="text-xl font-semibold mb-2">
          Welcome to the UniAI Dashboard
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          This is a placeholder for the main dashboard content. System status
          and key metrics will be displayed here.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;
