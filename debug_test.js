// API 連接測試腳本
const testAPI = async () => {
  console.log('開始 API 連接測試...');
  
  const endpoints = [
    'http://localhost:8000/api/v1/system/status',
    'http://localhost:8000/api/v1/system/metrics/detailed',
    'http://localhost:8000/api/v1/agents',
    'http://localhost:8000/api/v1/models',
    'http://localhost:8000/api/v1/images/history'
  ];
  
  for (const endpoint of endpoints) {
    try {
      console.log(`測試: ${endpoint}`);
      const response = await fetch(endpoint);
      if (response.ok) {
        const data = await response.json();
        console.log(`✅ ${endpoint} - 狀態: ${response.status}`);
        console.log(`   數據類型: ${typeof data}, 鍵: ${Object.keys(data).slice(0, 3).join(', ')}`);
      } else {
        console.log(`❌ ${endpoint} - 狀態: ${response.status}`);
      }
    } catch (error) {
      console.log(`❌ ${endpoint} - 錯誤: ${error.message}`);
    }
  }
  
  console.log('API 測試完成');
};

// 在瀏覽器控制台中運行
if (typeof window !== 'undefined') {
  window.testAPI = testAPI;
  console.log('在瀏覽器控制台中運行 testAPI() 來測試 API 連接');
} else {
  // Node.js 環境
  testAPI();
}