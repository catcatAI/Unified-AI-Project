const ZAI = require('z-ai-web-dev-sdk');

async function testZAI() {
  try {
    console.log('Testing ZAI SDK...');
    
    // Test 1: Create instance with config
    const zai = new ZAI.default({
      baseUrl: 'http://localhost:8080', // Try with a default base URL
      apiKey: 'test-key'
    });
    console.log('✅ ZAI instance created with config');
    
    // Test 2: Check config
    console.log('Config:', zai.config);
    
    // Test 3: Try to call a method
    try {
      const result = await zai.createChatCompletion({
        messages: [
          {
            role: 'user',
            content: 'Hello'
          }
        ]
      });
      console.log('✅ Chat completion successful:', result);
    } catch (chatError) {
      console.log('❌ Chat completion failed:', chatError.message);
      console.log('Error details:', chatError);
    }
    
  } catch (error) {
    console.error('❌ ZAI test failed:', error);
  }
}

testZAI();