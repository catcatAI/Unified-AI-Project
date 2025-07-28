import React, { useState, useEffect } from "react";
import { getHspServices, requestHspTask, getHspTaskStatus } from "../api/hsp";

const HSP = () => {
  const [services, setServices] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskResponses, setTaskResponses] = useState<any[]>([]);

  const fetchServices = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getHspServices();
      setServices(data);
    } catch (err) {
      setError("Failed to fetch HSP services.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, []);

  const handleSendTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const targetCapabilityId = formData.get("capabilityId") as string;
    const parametersStr = formData.get("parameters") as string;

    let parameters;
    try {
      parameters = JSON.parse(parametersStr);
    } catch (e) {
      alert("Invalid JSON for parameters.");
      return;
    }

    try {
      const response = await requestHspTask(targetCapabilityId, parameters);
      setTaskResponses((prev) => [response, ...prev]);
      if (response.correlation_id) {
        pollForTaskResult(response.correlation_id);
      }
    } catch (err) {
      alert("Failed to send HSP task.");
    }
  };

  const pollForTaskResult = (correlationId: string) => {
    const intervalId = setInterval(async () => {
      try {
        const statusResponse = await getHspTaskStatus(correlationId);
        if (
          statusResponse.status === "completed" ||
          statusResponse.status === "failed"
        ) {
          setTaskResponses((prev) =>
            prev.map((r) =>
              r.correlation_id === correlationId
                ? { ...r, ...statusResponse }
                : r,
            ),
          );
          clearInterval(intervalId);
        } else {
          setTaskResponses((prev) =>
            prev.map((r) =>
              r.correlation_id === correlationId
                ? { ...r, status: statusResponse.status }
                : r,
            ),
          );
        }
      } catch (error) {
        console.error("Polling error:", error);
        clearInterval(intervalId);
      }
    }, 3000);
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">HSP Network Services</h1>
        <button
          onClick={fetchServices}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <div className="text-red-500">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h2 className="text-xl font-semibold mb-2">Discovered Services</h2>
          <div className="space-y-2">
            {services.map((service) => (
              <div
                key={service.capability_id}
                className="p-3 bg-gray-100 dark:bg-gray-800 rounded"
              >
                <p className="font-bold">{service.name}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {service.description}
                </p>
                <p className="text-xs mt-1">ID: {service.capability_id}</p>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">Request HSP Task</h2>
          <form
            onSubmit={handleSendTask}
            className="space-y-3 p-3 bg-gray-100 dark:bg-gray-800 rounded"
          >
            <div>
              <label
                htmlFor="capabilityId"
                className="block text-sm font-medium"
              >
                Target Capability ID
              </label>
              <input
                type="text"
                name="capabilityId"
                id="capabilityId"
                className="mt-1 block w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
            <div>
              <label htmlFor="parameters" className="block text-sm font-medium">
                Parameters (JSON)
              </label>
              <textarea
                name="parameters"
                id="parameters"
                rows={3}
                className="mt-1 block w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
              ></textarea>
            </div>
            <button
              type="submit"
              className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Send Task
            </button>
          </form>

          <h2 className="text-xl font-semibold mt-4 mb-2">Task Responses</h2>
          <div className="space-y-2">
            {taskResponses.map((response, index) => (
              <div
                key={index}
                className="p-3 bg-gray-100 dark:bg-gray-800 rounded"
              >
                <p>
                  <strong>Status:</strong>{" "}
                  {response.status || response.status_message}
                </p>
                {response.correlation_id && (
                  <p>
                    <strong>Correlation ID:</strong> {response.correlation_id}
                  </p>
                )}
                {response.result_payload && (
                  <pre className="mt-2 p-2 bg-gray-200 dark:bg-gray-700 rounded text-xs">
                    {JSON.stringify(response.result_payload, null, 2)}
                  </pre>
                )}
                {response.error && (
                  <p className="text-red-500">
                    <strong>Error:</strong> {response.error}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HSP;
