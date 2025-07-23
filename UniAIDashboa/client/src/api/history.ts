import api from './api';

// Description: Get user's AI interaction history
// Endpoint: GET /api/history
// Request: { page?: number, limit?: number, serviceId?: string }
// Response: { history: Array<{ _id: string, serviceId: string, input: any, output: any, timestamp: string, processingTime: number, favorite: boolean }>, total: number }
export const getHistory = (params?: { page?: number; limit?: number; serviceId?: string }) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        history: [
          {
            _id: '1',
            serviceId: 'gpt-4',
            serviceName: 'GPT-4',
            input: 'Write a short story about AI',
            output: 'Once upon a time, in a world where artificial intelligence had become as common as smartphones...',
            timestamp: '2024-01-15T10:30:00Z',
            processingTime: 3.2,
            favorite: true,
            tokensUsed: 156
          },
          {
            _id: '2',
            serviceId: 'dalle-3',
            serviceName: 'DALL-E 3',
            input: 'A futuristic city with flying cars',
            output: 'https://picsum.photos/512/512?random=1',
            timestamp: '2024-01-15T09:15:00Z',
            processingTime: 15.7,
            favorite: false,
            tokensUsed: null
          },
          {
            _id: '3',
            serviceId: 'whisper',
            serviceName: 'Whisper',
            input: 'audio_file.mp3',
            output: 'This is the transcribed text from the audio file.',
            timestamp: '2024-01-15T08:45:00Z',
            processingTime: 8.4,
            favorite: false,
            tokensUsed: null
          }
        ],
        total: 3
      });
    }, 500);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.get('/api/history', { params });
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}

// Description: Toggle favorite status of a history item
// Endpoint: PUT /api/history/:id/favorite
// Request: { favorite: boolean }
// Response: { success: boolean }
export const toggleHistoryFavorite = (id: string, favorite: boolean) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 300);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.put(`/api/history/${id}/favorite`, { favorite });
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}

// Description: Delete a history item
// Endpoint: DELETE /api/history/:id
// Request: {}
// Response: { success: boolean }
export const deleteHistoryItem = (id: string) => {
  // Mocking the response
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 300);
  });
  // Uncomment the below lines to make an actual API call
  // try {
  //   return await api.delete(`/api/history/${id}`);
  // } catch (error) {
  //   throw new Error(error?.response?.data?.error || error.message);
  // }
}