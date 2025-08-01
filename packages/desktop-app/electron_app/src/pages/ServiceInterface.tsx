import React from "react";
import { useParams } from "react-router-dom";

export function ServiceInterface() {
  const { serviceId } = useParams<{ serviceId: string }>();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Service Interface</h1>
      <p className="text-gray-600 mb-4">Service ID: {serviceId}</p>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Service Details</h2>
        <p className="text-gray-600">
          This is a placeholder for the service interface. In a real application,
          this would show the specific interface for the selected service.
        </p>
      </div>
    </div>
  );
}