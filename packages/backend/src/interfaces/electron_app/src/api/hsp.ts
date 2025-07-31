import api from './api';

export const getHspServices = async () => {
  try {
    const response = await api.get('/api/v1/hsp/services');
    return response.data;
  } catch (error) {
    console.error('Error fetching HSP services:', error);
    throw error;
  }
};

export const requestHspTask = async (targetCapabilityId: string, parameters: any) => {
  try {
    const response = await api.post('/api/v1/hsp/tasks', { target_capability_id: targetCapabilityId, parameters });
    return response.data;
  } catch (error) {
    console.error('Error requesting HSP task:', error);
    throw error;
  }
};

export const getHspTaskStatus = async (correlationId: string) => {
    try {
        const response = await api.get(`/api/v1/hsp/tasks/${correlationId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching HSP task status for ${correlationId}:`, error);
        throw error;
    }
};
