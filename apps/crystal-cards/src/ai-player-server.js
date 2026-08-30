/**
 * ai-player-server.js — WebSocket server for AI player control
 * Runs inside Electron, exposes game state and accepts AI commands.
 *
 * Protocol:
 *   Client → Server: { type: "get_state" }
 *   Server → Client: { type: "game_state", state: {...} }
 *
 *   Client → Server: { type: "action", action: "click", x: 100, y: 200 }
 *   Client → Server: { type: "action", action: "drag", from: {x,y}, to: {x,y} }
 *   Client → Server: { type: "action", action: "sidebar_click", index: 0 }
 *   Client → Server: { type: "action", action: "draw_card" }
 *   Client → Server: { type: "action", action: "dialog_choice", index: 0 }
 *   Server → Client: { type: "action_result", success: true }
 */

const http = require('http');
const { WebSocketServer } = require('ws');

class AIPlayerServer {
  constructor() {
    this.port = 8765;
    this.server = null;
    this.wss = null;
    this.gameWindow = null;
  }

  setGameWindow(win) {
    this.gameWindow = win;
  }

  start() {
    this.server = http.createServer((req, res) => {
      // CORS headers
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

      if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
      }

      // REST API fallback
      if (req.url === '/state' && req.method === 'GET') {
        this.getState().then(state => {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(state));
        }).catch(err => {
          res.writeHead(500);
          res.end(JSON.stringify({ error: err.message }));
        });
        return;
      }

      if (req.url === '/action' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
          try {
            const action = JSON.parse(body);
            this.executeAction(action).then(result => {
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(result));
            }).catch(err => {
              res.writeHead(500);
              res.end(JSON.stringify({ error: err.message }));
            });
          } catch (e) {
            res.writeHead(400);
            res.end(JSON.stringify({ error: 'Invalid JSON' }));
          }
        });
        return;
      }

      res.writeHead(404);
      res.end('Not found');
    });

    this.wss = new WebSocketServer({ server: this.server });

    this.wss.on('connection', (ws) => {
      console.log('[AI Player] Client connected');

      ws.on('message', async (data) => {
        try {
          const msg = JSON.parse(data.toString());

          if (msg.type === 'get_state') {
            const state = await this.getState();
            ws.send(JSON.stringify({ type: 'game_state', state }));
          } else if (msg.type === 'action') {
            const result = await this.executeAction(msg);
            ws.send(JSON.stringify({ type: 'action_result', ...result }));
          } else if (msg.type === 'screenshot') {
            const screenshot = await this.getScreenshot();
            ws.send(JSON.stringify({ type: 'screenshot', data: screenshot }));
          }
        } catch (err) {
          ws.send(JSON.stringify({ type: 'error', message: err.message }));
        }
      });

      ws.on('close', () => {
        console.log('[AI Player] Client disconnected');
      });
    });

    this.server.listen(this.port, '127.0.0.1', () => {
      console.log(`[AI Player] Server listening on ws://127.0.0.1:${this.port}`);
    });
  }

  async getState() {
    if (!this.gameWindow) return { error: 'No game window' };

    // Execute JS in the game window to get state
    const state = await this.gameWindow.webContents.executeJavaScript(`
      (function() {
        if (!window.GameEngine) return { error: 'GameEngine not loaded' };
        const s = window.GameEngine.state;
        const cards = s.boardCards.map(c => {
          const t = window.GameEngine.getCardTemplate(c.templateId);
          return {
            id: c.id,
            templateId: c.templateId,
            name: t?.name || c.templateId,
            type: t?.type || 'unknown',
            icon: t?.icon || '?',
            x: Math.round(c.x),
            y: Math.round(c.y),
            hp: c.hp,
            maxHp: c.maxHp,
            count: c.count,
          };
        });
        const sidebar = s.sidebarCards.map(sc => {
          const t = window.GameEngine.getCardTemplate(sc.templateId);
          return {
            templateId: sc.templateId,
            name: t?.name || sc.templateId,
            type: t?.type || 'unknown',
            icon: t?.icon || '?',
            count: sc.count,
          };
        });
        const inventory = s.inventory.map(inv => {
          const t = window.GameEngine.getCardTemplate(inv.templateId);
          return {
            templateId: inv.templateId,
            name: t?.name || inv.templateId,
            type: t?.type || 'unknown',
            icon: t?.icon || '?',
            count: inv.count,
          };
        });
        return {
          hp: s.hp,
          maxHp: s.maxHp,
          sanity: s.sanity,
          gold: s.gold,
          knowledge: s.knowledge,
          day: s.day,
          timeOfDay: s.timeOfDay,
          paused: s.paused,
          boardCards: cards,
          sidebarCards: sidebar,
          inventory: inventory,
          unlockedLocations: s.unlockedLocations,
          flags: s.flags,
          bonds: s.bonds,
        };
      })()
    `);

    return state;
  }

  async executeAction(action) {
    if (!this.gameWindow) return { success: false, error: 'No game window' };

    switch (action.action) {
      case 'click':
        return await this.gameWindow.webContents.executeJavaScript(`
          (function() {
            const el = document.elementFromPoint(${action.x}, ${action.y});
            if (el && el.classList.contains('card')) {
              el.dispatchEvent(new MouseEvent('dblclick', { clientX: ${action.x}, clientY: ${action.y}, bubbles: true }));
              return { success: true, clicked: el.dataset.cardId };
            }
            return { success: false, error: 'No card at position' };
          })()
        `);

      case 'drag':
        return await this.gameWindow.webContents.executeJavaScript(`
          (function() {
            const fromEl = document.elementFromPoint(${action.from.x}, ${action.from.y});
            const toEl = document.elementFromPoint(${action.to.x}, ${action.to.y});
            if (fromEl && fromEl.classList.contains('card')) {
              const cardId = parseInt(fromEl.dataset.cardId);
              // Find the card in game state and move it
              const card = window.GameEngine.state.boardCards.find(c => c.id === cardId);
              if (card) {
                card.x = ${action.to.x};
                card.y = ${action.to.y};
                // Trigger visual update
                fromEl.style.left = card.x + 'px';
                fromEl.style.top = card.y + 'px';
                return { success: true, cardId };
              }
            }
            return { success: false, error: 'No card to drag' };
          })()
        `);

      case 'sidebar_click':
        return await this.gameWindow.webContents.executeJavaScript(`
          (function() {
            const cards = document.querySelectorAll('#available-cards .sidebar-card');
            if (cards[${action.index}]) {
              cards[${action.index}].click();
              return { success: true };
            }
            return { success: false, error: 'No sidebar card at index' };
          })()
        `);

      case 'draw_card':
        return await this.gameWindow.webContents.executeJavaScript(`
          (function() {
            document.getElementById('btn-draw').click();
            return { success: true };
          })()
        `);

      case 'dialog_choice':
        return await this.gameWindow.webContents.executeJavaScript(`
          (function() {
            const choices = document.querySelectorAll('#dialog-choices .dialog-choice:not(.disabled)');
            if (choices[${action.index}]) {
              choices[${action.index}].click();
              return { success: true, text: choices[${action.index}].textContent.trim() };
            }
            return { success: false, error: 'No available choice at index' };
          })()
        `);

      case 'stack_cards':
        // Stack two cards by ID
        return await this.gameWindow.webContents.executeJavaScript(`
          (function() {
            const cardA = window.GameEngine.state.boardCards.find(c => c.id === ${action.cardA});
            const cardB = window.GameEngine.state.boardCards.find(c => c.id === ${action.cardB});
            if (cardA && cardB) {
              const result = window.GameEngine.tryStack(cardA, cardB);
              if (result) {
                return { success: true, result: { type: result.type, message: result.message || '' } };
              }
              return { success: false, error: 'Cannot stack these cards' };
            }
            return { success: false, error: 'Card not found' };
          })()
        `);

      case 'pause':
        return await this.gameWindow.webContents.executeJavaScript(`
          window.GameEngine.state.paused = !window.GameEngine.state.paused;
          { success: true, paused: window.GameEngine.state.paused }
        `);

      default:
        return { success: false, error: `Unknown action: ${action.action}` };
    }
  }

  async getScreenshot() {
    if (!this.gameWindow) return null;
    const image = await this.gameWindow.webContents.capturePage();
    return image.toDataURL();
  }

  stop() {
    if (this.wss) this.wss.close();
    if (this.server) this.server.close();
  }
}

module.exports = { AIPlayerServer };
