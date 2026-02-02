import api from './api';

// Description: Upload project files for analysis
// Endpoint: POST /api/code-analysis/upload
// Request: { files?: FileList, githubUrl?: string }
// Response: { success: boolean, projectId: string, message: string }
export const uploadProject = (data: { files?: FileList | null; githubUrl?: string }) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        projectId: 'proj_' + Math.random().toString(36).substr(2, 9),
        message: 'Project uploaded successfully'
      });
    }, 1000);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   const formData = new FormData();
  //   if (data.files) {
  //     Array.from(data.files).forEach(file => formData.append('files', file));
  //   }
  //   if (data.githubUrl) {
  //     formData.append('githubUrl', data.githubUrl);
  //   }
  //   return await api.post('/api/code-analysis/upload', formData, {
  //     headers: { 'Content-Type': 'multipart/form-data' }
  //   });
  // } catch (error) {
  //   throw new Error(error?.response?.data?.message || error.message);
  // }
};

// Description: Get project analysis results
// Endpoint: GET /api/code-analysis/project/:id
// Request: { projectId: string }
// Response: { project: ProjectAnalysis }
export const getProjectAnalysis = (projectId: string) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        _id: projectId,
        name: 'Sample Project',
        description: 'A sample JavaScript project for demonstration',
        fileCount: 42,
        totalSize: '2.3 MB',
        totalIssues: 15,
        criticalIssues: 3,
        warningIssues: 8,
        infoIssues: 4,
        complexityScore: 67,
        analyzedAt: new Date().toISOString(),
        languages: [
          { name: 'JavaScript', percentage: 65 },
          { name: 'TypeScript', percentage: 25 },
          { name: 'CSS', percentage: 8 },
          { name: 'HTML', percentage: 2 }
        ],
        dependencies: [
          { name: 'react', version: '18.2.0' },
          { name: 'lodash', version: '4.17.21' },
          { name: 'axios', version: '1.4.0' },
          { name: 'express', version: '4.18.2' },
          { name: 'mongoose', version: '7.3.0' }
        ],
        entryPoints: [
          { path: 'src/index.js' },
          { path: 'src/App.js' },
          { path: 'server/server.js' }
        ],
        files: [
          { path: 'src/index.js', content: '// Main entry point\nimport React from "react";\nimport ReactDOM from "react-dom";\nimport App from "./App";\n\nReactDOM.render(<App />, document.getElementById("root"));' },
          { path: 'src/App.js', content: '// Main App component\nimport React from "react";\n\nfunction App() {\n  return (\n    <div className="App">\n      <h1>Hello World</h1>\n    </div>\n  );\n}\n\nexport default App;' },
          { path: 'src/utils/helpers.js', content: '// Utility functions\nexport const formatDate = (date) => {\n  return date.toLocaleDateString();\n};\n\nexport const validateEmail = (email) => {\n  const regex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;\n  return regex.test(email);\n};' }
        ],
        issues: [
          {
            _id: 'issue_1',
            title: 'Potential XSS Vulnerability',
            description: 'User input is not properly sanitized before rendering',
            severity: 'critical',
            category: 'security',
            file: 'src/App.js',
            line: 15,
            suggestion: 'Use proper input sanitization or escape user content before rendering'
          },
          {
            _id: 'issue_2',
            title: 'Unused Variable',
            description: 'Variable "unusedVar" is declared but never used',
            severity: 'warning',
            category: 'style',
            file: 'src/utils/helpers.js',
            line: 8,
            suggestion: 'Remove the unused variable or use it in your code'
          },
          {
            _id: 'issue_3',
            title: 'Missing Error Handling',
            description: 'Async function lacks proper error handling',
            severity: 'warning',
            category: 'bug',
            file: 'src/index.js',
            line: 23,
            suggestion: 'Add try-catch blocks around async operations'
          }
        ]
      });
    }, 2000);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.get(`/api/code-analysis/project/${projectId}`);
  // } catch (error) {
  //   throw new Error(error?.response?.data?.message || error.message);
  // }
};

// Description: Get project history for current user
// Endpoint: GET /api/code-analysis/history
// Request: {}
// Response: { projects: Array<ProjectSummary> }
export const getProjectHistory = () => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        projects: [
          {
            _id: 'proj_1',
            name: 'E-commerce Frontend',
            description: 'React-based e-commerce application',
            totalIssues: 23,
            fileCount: 67,
            riskLevel: 'medium',
            analyzedAt: new Date(Date.now() - 86400000).toISOString() // 1 day ago
          },
          {
            _id: 'proj_2',
            name: 'API Server',
            description: 'Node.js REST API with Express',
            totalIssues: 8,
            fileCount: 34,
            riskLevel: 'low',
            analyzedAt: new Date(Date.now() - 172800000).toISOString() // 2 days ago
          },
          {
            _id: 'proj_3',
            name: 'Legacy Codebase',
            description: 'Old PHP application requiring modernization',
            totalIssues: 156,
            fileCount: 203,
            riskLevel: 'high',
            analyzedAt: new Date(Date.now() - 604800000).toISOString() // 1 week ago
          }
        ]
      });
    }, 800);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.get('/api/code-analysis/history');
  // } catch (error) {
  //   throw new Error(error?.response?.data?.message || error.message);
  // }
};

// Description: Delete a project from history
// Endpoint: DELETE /api/code-analysis/project/:id
// Request: { projectId: string }
// Response: { success: boolean, message: string }
export const deleteProject = (projectId: string) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        message: 'Project deleted successfully'
      });
    }, 500);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.delete(`/api/code-analysis/project/${projectId}`);
  // } catch (error) {
  //   throw new Error(error?.response?.data?.message || error.message);
  // }
};

// Description: Generate analysis report
// Endpoint: POST /api/code-analysis/report
// Request: { projectId: string, format: string, options: object }
// Response: { reportUrl: string, downloadUrl: string }
export const generateReport = (data: { projectId: string; format: string; options: any }) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        reportUrl: '/reports/sample-report.pdf',
        downloadUrl: '/api/reports/download/sample-report.pdf'
      });
    }, 2000);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.post('/api/code-analysis/report', data);
  // } catch (error) {
  //   throw new Error(error?.response?.data?.message || error.message);
  // }
};
