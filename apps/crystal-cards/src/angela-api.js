/**
 * angela-api.js — Angela AI Backend Integration
 * Connects to the backend WebSocket/HTTP API for:
 * 1. Dynamic NPC dialogue generation (when templates run out)
 * 2. Text-to-speech for character voices
 * 3. Story event generation
 */

class AngelaGameAPI {
  constructor() {
    this.wsUrl = 'ws://127.0.0.1:8000/ws';
    this.httpUrl = 'http://127.0.0.1:8000';
    this.ws = null;
    this.connected = false;
    this.sessionId = null;
  }

  async connect() {
    try {
      this.ws = new WebSocket(this.wsUrl);
      return new Promise((resolve, reject) => {
        this.ws.onopen = () => {
          // Send handshake
          this.ws.send(JSON.stringify({
            session_id: '',
            client_type: 'crystal-cards',
            client_version: '1.0.0',
          }));
        };
        this.ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.type === 'connected') {
            this.connected = true;
            this.sessionId = msg.session_id;
            resolve(true);
          }
        };
        this.ws.onerror = () => resolve(false);
        setTimeout(() => resolve(false), 3000);
      });
    } catch (e) {
      return false;
    }
  }

  /**
   * Generate dynamic NPC dialogue using Angela AI
   * Falls back to static template if Angela is unavailable
   */
  async generateNPCDialogue(characterName, playerInput, context = {}) {
    if (!this.connected) {
      return this._fallbackDialogue(characterName, playerInput);
    }

    try {
      const prompt = `你是遊戲中的NPC「${characterName}」。${context.backstory || ''}
玩家說：「${playerInput}」
請用角色的語氣回應（1-2句話）。`;

      const response = await fetch(`${this.httpUrl}/chat/unified`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: prompt,
          context: {
            source: 'crystal-cards-game',
            character: characterName,
            emotion: context.emotion || 'neutral',
          },
        }),
      });

      const data = await response.json();
      return {
        text: data.response || data.response_text || data.message || '',
        source: 'angela',
      };
    } catch (e) {
      return this._fallbackDialogue(characterName, playerInput);
    }
  }

  /**
   * Generate ambient description for a location
   */
  async generateAmbience(locationName, timeOfDay, weather = 'clear') {
    if (!this.connected) {
      return this._fallbackAmbience(locationName, timeOfDay);
    }

    try {
      const prompt = `描述「${locationName}」在${timeOfDay}時的環境氣氛（1句話，30字以內）。`;

      const response = await fetch(`${this.httpUrl}/chat/unified`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: prompt,
          context: { source: 'crystal-cards-ambience' },
        }),
      });

      const data = await response.json();
      return data.response || data.response_text || '';
    } catch (e) {
      return this._fallbackAmbience(locationName, timeOfDay);
    }
  }

  /**
   * Text-to-speech for character dialogue
   */
  async textToSpeech(text, characterName) {
    if (!this.connected) return null;

    try {
      const voiceMap = {
        '晞咕萊雅': 'zh-CN-XiaoxiaoNeural',
        '紅': 'zh-CN-YunxiNeural',
        '織織': 'zh-CN-XiaoxiaoNeural',
        '宿曉': 'zh-CN-XiaoyiNeural',
        '姬路': 'zh-CN-XiaoxiaoNeural',
        '吉普莉爾': 'zh-CN-YunxiNeural',
        '露露': 'zh-CN-XiaoyiNeural',
        '暈咔繆露': 'zh-CN-XiaoxiaoNeural',
        '旁白': 'zh-CN-XiaoxiaoNeural',
      };

      const response = await fetch(`${this.httpUrl}/audio/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          voice: voiceMap[characterName] || 'zh-CN-XiaoxiaoNeural',
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        return URL.createObjectURL(blob);
      }
    } catch (e) {
      // TTS not available
    }
    return null;
  }

  // ── Fallbacks (when Angela is offline) ──

  _fallbackDialogue(characterName, playerInput) {
    const responses = {
      '晞咕萊雅': '她看著你，沒有說話。',
      '紅': '「嗯？」',
      '織織': '貓耳動了動。',
      '宿曉': '她推了推眼鏡。',
      '姬路': '她點了點頭。',
      '吉普莉爾': '翅膀微微張開。',
      '露露': '她翻看手邊的帳本。',
      '暈咔繆露': '她的表情有些恍惚。',
    };
    return {
      text: responses[characterName] || '對方沉默了一會兒。',
      source: 'fallback',
    };
  }

  _fallbackAmbience(locationName, timeOfDay) {
    const ambiances = {
      '聖十字校園': { morning: '走廊裡開始有人走動。', afternoon: '安靜得不正常。', evening: '走廊空了。', night: '完全的黑暗。' },
      '鏡湖': { morning: '湖面映著晨光。', afternoon: '湖水清澈見底。', evening: '水面泛著夕陽。', night: '湖底有微光閃爍。' },
      '卡洛夫角': { morning: '攤位開始營業。', afternoon: '叫賣聲此起彼落。', evening: '市集漸漸安靜。', night: '只剩下幾盞燈。' },
      '迴廊': { morning: '概念流開始活躍。', afternoon: '數據交織得更快。', evening: '迴廊安靜下來。', night: '只剩下低頻嗡鳴。' },
      '便利店': { morning: '自動門打開。', afternoon: '冷氣嗡嗡作響。', evening: '霓虹燈亮了。', night: '只有值班燈。' },
    };
    const loc = ambiances[locationName] || {};
    return loc[timeOfDay] || '一片寂靜。';
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.connected = false;
    }
  }
}

// Singleton
window.angelaAPI = new AngelaGameAPI();
