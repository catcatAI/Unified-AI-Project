import React from "react";
import { useAuth } from "../contexts/AuthContext";

export function Settings() {
  const { user, logout } = useAuth();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Account Information</h2>
          <div className="space-y-2">
            <p><strong>Name:</strong> {user?.name}</p>
            <p><strong>Email:</strong> {user?.email}</p>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Preferences</h2>
          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" />
                Enable notifications
              </label>
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" />
                Dark mode
              </label>
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" />
                Auto-save
              </label>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Actions</h2>
          <button
            onClick={logout}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}