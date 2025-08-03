// Placeholder for Code Analysis API service
// In a real implementation, this would make API calls to the backend.

export const uploadProjectForAnalysis = async (data: { files?: FileList | null; githubUrl?: string }) => {
  console.log("Attempting to upload project for analysis (mocked):", data);
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        projectId: 'mock_proj_' + Math.random().toString(36).substr(2, 9),
        message: '功能開發中：專案以上傳，正在排隊分析。'
      });
    }, 1000);
  });
};

export const getAnalysisResult = async (projectId: string) => {
    console.log(`Fetching analysis result for project ${projectId} (mocked)`);
    // Mocking the response
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                status: "completed",
                summary: "功能開發中：這是一個模擬的分析摘要。",
                issues: [
                    { id: 1, severity: "critical", description: "檢測到潛在的安全漏洞（模擬）。" },
                    { id: 2, severity: "warning", description: "發現了未使用的變數（模擬）。" }
                ]
            });
        }, 1500);
    });
};
