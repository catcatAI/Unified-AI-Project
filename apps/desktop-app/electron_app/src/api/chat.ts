import api from './api';

export const startSession = async () => {
  try {
    const response = await api.post('/api/v1/session/start', {});
    return response.data;
  } catch (error) {
    console.error('Error starting session:', error);
    throw error;
  }
};

export const sendMessage = async (text: string, sessionId: string, userId?: string) => {
  try {
    const response = await api.post('/api/v1/chat', { text, session_id: sessionId, user_id: userId });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};
