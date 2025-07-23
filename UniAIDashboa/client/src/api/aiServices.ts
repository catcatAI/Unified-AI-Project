import api from './api';

// Description: Get all available AI services
// Endpoint: GET /api/ai-services
// Request: {}
// Response: { services: Array<{ id: string, name: string, category: string, description: string, status: string, usage: number, icon: string }> }
export const getAIServices = () => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        services: [
          {
            id: 'gpt-4',
            name: 'GPT-4',
            category: 'Text & Language',
            description: 'Advanced language model for text generation, analysis, and conversation',
            status: 'active',
            usage: 1234,
            icon: 'MessageSquare',
            pricing: '$0.03/1K tokens',
            processingTime: '2-5 seconds'
          },
          {
            id: 'dalle-3',
            name: 'DALL-E 3',
            category: 'Image & Vision',
            description: 'Generate high-quality images from text descriptions',
            status: 'active',
            usage: 456,
            icon: 'Image',
            pricing: '$0.04/image',
            processingTime: '10-30 seconds'
          },
          {
            id: 'whisper',
            name: 'Whisper',
            category: 'Audio & Speech',
            description: 'Convert speech to text with high accuracy',
            status: 'active',
            usage: 789,
            icon: 'Mic',
            pricing: '$0.006/minute',
            processingTime: '5-15 seconds'
          },
          {
            id: 'claude',
            name: 'Claude',
            category: 'Text & Language',
            description: 'Anthropic\'s AI assistant for analysis and reasoning',
            status: 'active',
            usage: 567,
            icon: 'MessageSquare',
            pricing: '$0.025/1K tokens',
            processingTime: '3-7 seconds'
          },
          {
            id: 'stable-diffusion',
            name: 'Stable Diffusion',
            category: 'Image & Vision',
            description: 'Open-source image generation model',
            status: 'active',
            usage: 234,
            icon: 'Image',
            pricing: '$0.02/image',
            processingTime: '15-45 seconds'
          },
          {
            id: 'tts',
            name: 'Text-to-Speech',
            category: 'Audio & Speech',
            description: 'Convert text to natural-sounding speech',
            status: 'active',
            usage: 345,
            icon: 'Volume2',
            pricing: '$0.015/1K chars',
            processingTime: '3-10 seconds'
          }
        ]
      });
    }, 500);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.get('/api/ai-services');
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}

// Description: Execute AI service with parameters
// Endpoint: POST /api/ai-services/execute
// Request: { serviceId: string, parameters: object, input: string | object }
// Response: { result: any, processingTime: number, tokensUsed?: number }
export const executeAIService = (data: { serviceId: string; parameters: object; input: string | object }) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      const mockResults = {
        'gpt-4': {
          result: "This is a sample response from GPT-4. The model has processed your input and generated this comprehensive response that demonstrates the capabilities of advanced language understanding and generation.",
          processingTime: 3.2,
          tokensUsed: 156
        },
        'dalle-3': {
          result: "https://picsum.photos/512/512?random=" + Math.random(),
          processingTime: 15.7,
          tokensUsed: null
        },
        'whisper': {
          result: "This is the transcribed text from your audio file. The speech recognition has been processed with high accuracy.",
          processingTime: 8.4,
          tokensUsed: null
        }
      };
      
      resolve(mockResults[data.serviceId as keyof typeof mockResults] || {
        result: "Service executed successfully",
        processingTime: 5.0,
        tokensUsed: 100
      });
    }, Math.random() * 3000 + 1000);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.post('/api/ai-services/execute', data);
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}

// Description: Get service usage statistics
// Endpoint: GET /api/ai-services/usage
// Request: {}
// Response: { usage: Array<{ serviceId: string, count: number, cost: number, date: string }> }
export const getServiceUsage = () => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        usage: [
          { serviceId: 'gpt-4', count: 1234, cost: 37.02, date: '2024-01-15' },
          { serviceId: 'dalle-3', count: 456, cost: 18.24, date: '2024-01-15' },
          { serviceId: 'whisper', count: 789, cost: 4.73, date: '2024-01-15' },
          { serviceId: 'claude', count: 567, cost: 14.18, date: '2024-01-15' },
        ]
      });
    }, 500);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.get('/api/ai-services/usage');
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}