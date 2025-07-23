import api from './api';

// Description: Get user's workflows
// Endpoint: GET /api/workflows
// Request: {}
// Response: { workflows: Array<{ _id: string, name: string, description: string, steps: Array<any>, createdAt: string, lastUsed: string }> }
export const getWorkflows = () => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        workflows: [
          {
            _id: '1',
            name: 'Content Creation Pipeline',
            description: 'Generate text with GPT-4, then create an image with DALL-E',
            steps: [
              { serviceId: 'gpt-4', parameters: { temperature: 0.7 } },
              { serviceId: 'dalle-3', parameters: { size: '1024x1024' } }
            ],
            createdAt: '2024-01-10T10:00:00Z',
            lastUsed: '2024-01-15T14:30:00Z',
            executions: 23
          },
          {
            _id: '2',
            name: 'Audio Processing',
            description: 'Transcribe audio with Whisper, then summarize with Claude',
            steps: [
              { serviceId: 'whisper', parameters: {} },
              { serviceId: 'claude', parameters: { task: 'summarize' } }
            ],
            createdAt: '2024-01-12T15:20:00Z',
            lastUsed: '2024-01-14T11:15:00Z',
            executions: 8
          }
        ]
      });
    }, 500);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.get('/api/workflows');
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}

// Description: Create a new workflow
// Endpoint: POST /api/workflows
// Request: { name: string, description: string, steps: Array<any> }
// Response: { workflow: object, success: boolean }
export const createWorkflow = (data: { name: string; description: string; steps: Array<any> }) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        workflow: {
          _id: Date.now().toString(),
          ...data,
          createdAt: new Date().toISOString(),
          lastUsed: null,
          executions: 0
        },
        success: true
      });
    }, 500);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.post('/api/workflows', data);
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}

// Description: Execute a workflow
// Endpoint: POST /api/workflows/:id/execute
// Request: { input: any }
// Response: { results: Array<any>, success: boolean }
export const executeWorkflow = (id: string, input: any) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        results: [
          { step: 1, serviceId: 'gpt-4', result: 'Generated text content...' },
          { step: 2, serviceId: 'dalle-3', result: 'https://picsum.photos/512/512?random=' + Math.random() }
        ],
        success: true
      });
    }, 3000);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.post(`/api/workflows/${id}/execute`, { input });
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}