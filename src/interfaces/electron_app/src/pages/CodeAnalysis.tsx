import React, { useState } from 'react';
import { uploadProjectForAnalysis, getAnalysisResult } from '../api/codeAnalysis';

const CodeAnalysis = () => {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setIsLoading(true);
      const response = await uploadProjectForAnalysis({ files });
      alert(response.message);
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Code Inspector</h1>
      <div className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
        <h2 className="text-xl font-semibold mb-2">Upload Project</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Upload your project files for analysis. This feature is currently under development.
        </p>
        <input type="file" multiple onChange={handleFileUpload} disabled={isLoading} />
        {isLoading && <p className="mt-2">Uploading and analyzing...</p>}
      </div>
    </div>
  );
};

export default CodeAnalysis;
