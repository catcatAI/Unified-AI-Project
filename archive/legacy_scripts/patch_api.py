import os

file_path = 'apps/frontend-dashboard/src/lib/api.ts'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_method = """
  async sendMSCUMessage(content: string): Promise<any> {
    try {
      const response = await this.axiosInstance.post('/chat/mscu', {
        message: content,
      });
      return {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
        model: 'MSCU-Hybrid',
        metadata: response.data.metadata || {} 
      };
    } catch (error) {
      console.error('Failed to send MSCU message:', error);
      throw error;
    }
  }
"""

# Insert after sendChatMessage closing brace
target = """    } catch (error) {
      console.error('Failed to send chat message:', error);
      throw error;
    }
  }"""

if "sendMSCUMessage" not in content:
    new_content = content.replace(target, target + "\n" + new_method)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched api.ts")
else:
    print("api.ts already contains sendMSCUMessage")
