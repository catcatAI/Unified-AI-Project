import axios from 'axios';
import client from './client';

jest.mock('axios');

describe('API Client - healthCheck', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('returns data from /api/v1/health', async () => {
    const mockData = { status: 'healthy' };
    axios.get.mockResolvedValueOnce({ data: mockData });

    const result = await client.healthCheck();
    expect(result).toEqual(mockData);
    expect(axios.get).toHaveBeenCalledWith('http://127.0.0.1:8000/api/v1/health');
  });
});
