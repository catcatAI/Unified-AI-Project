/**
 * renderer.js — Visual rendering, drag-drop, sidebar, HUD
 * Bridges GameEngine data to DOM elements
 */

(function () {
  const E = window.GameEngine;
  const S = window.sounds;

  // ── DOM refs ──
  const board = document.getElementById('board');
  const sidebarContent = document.getElementById('sidebar-content');
  const availableCards = document.getElementById('available-cards');
  const inventoryCards = document.getElementById('inventory-cards');
  const dayDisplay = document.getElementById('day-display');
  const timeDisplay = document.getElementById('time-display');
  const hpDisplay = document.getElementById('hp-display');
  const sanDisplay = document.getElementById('san-display');
  const goldDisplay = document.getElementById('gold-display');
  const btnPause = document.getElementById('btn-pause');
  const btnSpeed = document.getElementById('btn-speed');
  const btnDraw = document.getElementById('btn-draw');
  const drawCostValue = document.getElementById('draw-cost-value');
  const btnSettings = document.getElementById('btn-settings');
  const settingsOverlay = document.getElementById('settings-overlay');
  const settingsClose = document.getElementById('settings-close');
  const settingVolume = document.getElementById('setting-volume');
  const volumeValue = document.getElementById('volume-value');
  const notification = document.getElementById('notification');

  // ── Card DOM elements map ──
  const cardElements = new Map(); // cardId -> DOM element

  // ── Drag state ──
  let dragState = {
    active: false,
    cardId: null,
    offsetX: 0,
    offsetY: 0,
    startX: 0,
    startY: 0,
  };

  // ═══════════════════════════════════════════════════════
  // Card DOM Creation
  // ═══════════════════════════════════════════════════════
  function createCardElement(card) {
    const template = E.getCardTemplate(card.templateId);
    if (!template) return null;

    const el = document.createElement('div');
    el.className = 'card';
    el.dataset.cardId = card.id;
    el.dataset.type = template.type;

    el.innerHTML = `
      <div class="card-icon">${template.icon || '❓'}</div>
      <div class="card-name">${template.name}</div>
      <div class="card-subtitle">${template.type === 'character' ? (template.role || '') : (template.category || '')}</div>
      ${card.hp !== null ? `<div class="card-hp-bar"><div class="card-hp-fill" style="width:${(card.hp / card.maxHp) * 100}%; background:${template.color || '#4CAF50'}"></div></div>` : ''}
      ${card.count > 1 ? `<div class="card-stack-count">${card.count}</div>` : ''}
    `;

    // Position
    el.style.left = card.x + 'px';
    el.style.top = card.y + 'px';

    // Location cards are generating
    if (template.type === 'location' && template.resourceRate > 0) {
      el.classList.add('generating');
    }

    // Events
    el.addEventListener('mousedown', onCardMouseDown);
    el.addEventListener('mouseenter', onCardMouseEnter);
    el.addEventListener('mouseleave', onCardMouseLeave);
    el.addEventListener('dblclick', onCardDblClick);
    el.addEventListener('contextmenu', onCardContextMenu);

    board.appendChild(el);
    cardElements.set(card.id, el);
    return el;
  }

  function updateCardElement(card) {
    const el = cardElements.get(card.id);
    if (!el) return;

    const template = E.getCardTemplate(card.templateId);
    if (!template) return;

    el.style.left = card.x + 'px';
    el.style.top = card.y + 'px';

    // Update HP bar
    const hpFill = el.querySelector('.card-hp-fill');
    if (hpFill && card.hp !== null) {
      hpFill.style.width = `${(card.hp / card.maxHp) * 100}%`;
    }

    // Update stack count
    let stackEl = el.querySelector('.card-stack-count');
    if (card.count > 1) {
      if (!stackEl) {
        stackEl = document.createElement('div');
        stackEl.className = 'card-stack-count';
        el.appendChild(stackEl);
      }
      stackEl.textContent = card.count;
    } else if (stackEl) {
      stackEl.remove();
    }
  }

  function removeCardElement(cardId) {
    const el = cardElements.get(cardId);
    if (el) {
      el.classList.add('destroying');
      setTimeout(() => {
        el.remove();
        cardElements.delete(cardId);
      }, 400);
    }
  }

  // ═══════════════════════════════════════════════════════
  // Drag & Drop
  // ═══════════════════════════════════════════════════════
  function onCardMouseDown(e) {
    if (e.button !== 0) return; // Left click only
    e.preventDefault();
    e.stopPropagation();

    const cardId = parseInt(e.currentTarget.dataset.cardId);
    const card = E.state.boardCards.find(c => c.id === cardId);
    if (!card) return;

    dragState.active = true;
    dragState.cardId = cardId;
    dragState.offsetX = e.clientX - card.x;
    dragState.offsetY = e.clientY - card.y;
    dragState.startX = card.x;
    dragState.startY = card.y;

    const el = cardElements.get(cardId);
    if (el) {
      el.classList.add('dragging');
      el.style.zIndex = 1000;
    }

    S.cardPickup();

    document.addEventListener('mousemove', onDragMove);
    document.addEventListener('mouseup', onDragEnd);
  }

  function onDragMove(e) {
    if (!dragState.active) return;

    const card = E.state.boardCards.find(c => c.id === dragState.cardId);
    if (!card) return;

    card.x = e.clientX - dragState.offsetX;
    card.y = e.clientY - dragState.offsetY;

    const el = cardElements.get(dragState.cardId);
    if (el) {
      el.style.left = card.x + 'px';
      el.style.top = card.y + 'px';
    }

    // Highlight potential stack targets
    const target = E.findStackAt(card.x, card.y, card.id);
    cardElements.forEach((el, id) => {
      if (id !== dragState.cardId) {
        el.classList.remove('stack-target');
      }
    });
    if (target) {
      const targetEl = cardElements.get(target.id);
      if (targetEl) targetEl.classList.add('stack-target');
    }
  }

  function onDragEnd(e) {
    document.removeEventListener('mousemove', onDragMove);
    document.removeEventListener('mouseup', onDragEnd);

    if (!dragState.active) return;

    const card = E.state.boardCards.find(c => c.id === dragState.cardId);
    if (!card) {
      dragState.active = false;
      return;
    }

    const el = cardElements.get(dragState.cardId);
    if (el) {
      el.classList.remove('dragging');
      el.style.zIndex = '';
    }

    // Remove stack target highlights
    cardElements.forEach((el) => el.classList.remove('stack-target'));

    // Check for stacking
    const target = E.findStackAt(card.x, card.y, card.id);
    if (target) {
      const result = E.tryStack(card, target);
      if (result) {
        handleStackResult(result, target);
      }
    }

    S.cardPlace();

    dragState.active = false;
    dragState.cardId = null;
  }

  // ═══════════════════════════════════════════════════════
  // Stack Result Handling
  // ═══════════════════════════════════════════════════════
  function handleStackResult(result, targetCard) {
    switch (result.type) {
      case 'stack':
        showNotification(result.message);
        updateCardElement(targetCard);
        S.collect();
        break;
      case 'craft':
        showNotification(result.message);
        S.craft();
        if (result.card) {
          createCardElement(result.card);
        }
        refreshAllCards();
        break;
      case 'dialogue':
        S.dialogOpen();
        window.DialogSystem.showDialogue(result.dialogueId);
        break;
      case 'combat':
        S.combatHit();
        showCombatPanel(result);
        break;
      case 'use':
        showNotification(result.message);
        updateCardElement(targetCard);
        S.collect();
        break;
    }
  }

  // ═══════════════════════════════════════════════════════
  // Combat Panel
  // ═══════════════════════════════════════════════════════
  function showCombatPanel(result) {
    const overlay = document.getElementById('combat-overlay');
    const title = document.getElementById('combat-title');
    const info = document.getElementById('combat-info');
    const log = document.getElementById('combat-log');
    const btnAttack = document.getElementById('btn-attack');
    const btnFlee = document.getElementById('btn-flee');

    const attacker = result.attacker;
    const defender = result.defender;

    title.textContent = `⚔️ ${attacker?.name || '你'} vs ${defender.name}`;
    info.innerHTML = `
      <div>❤️ 你: ${E.state.hp}/${E.state.maxHp}</div>
      <div>👾 ${defender.name}: ${defender.stats.hp} HP</div>
    `;
    log.innerHTML = '';
    overlay.classList.remove('hidden');

    const doCombat = () => {
      const combatResult = E.executeCombat(attacker, defender, result.attackerCard, result.defenderCard);

      combatResult.results.forEach(r => {
        const entry = document.createElement('div');
        entry.className = 'combat-log-entry';
        entry.innerHTML = `<span class="${r.type}">${r.text}</span>`;
        log.appendChild(entry);
      });

      info.innerHTML = `
        <div>❤️ 你: ${E.state.hp}/${E.state.maxHp}</div>
        <div>👾 ${defender.name}: ${result.defenderCard.hp || 0} HP</div>
      `;

      if (combatResult.won || combatResult.gameOver) {
        setTimeout(() => overlay.classList.add('hidden'), 800);
        refreshAllCards();
      }

      if (combatResult.gameOver) {
        showNotification('💀 遊戲結束！重新開始...');
        setTimeout(() => {
          E.initNewGame();
          refreshAllCards();
        }, 2000);
      }
    };

    btnAttack.onclick = () => {
      S.combatHit();
      doCombat();
    };
    btnFlee.onclick = () => {
      if (Math.random() < 0.6) {
        showNotification('🏃 成功逃跑！');
        overlay.classList.add('hidden');
      } else {
        showNotification('❌ 逃跑失敗！');
        doCombat();
      }
    };
  }

  // ═══════════════════════════════════════════════════════
  // Card Double-Click (Info / Place from sidebar)
  // ═══════════════════════════════════════════════════════
  // ── Context Menu ──
  let activeContextMenu = null;

  function closeContextMenu() {
    if (activeContextMenu) { activeContextMenu.remove(); activeContextMenu = null; }
  }

  function onCardContextMenu(e) {
    e.preventDefault();
    closeContextMenu();
    const cardId = parseInt(e.currentTarget.dataset.cardId);
    const card = E.state.boardCards.find(c => c.id === cardId);
    if (!card) return;
    const template = E.getCardTemplate(card.templateId);
    if (!template) return;

    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';

    // Build actions based on card type
    const actions = [];
    if (template.type === 'location') {
      actions.push({ text: '🗺️ 探索（解鎖鄰近地點）', fn: () => {
        const newUnlocks = E.unlockAdjacentLocations(card.templateId);
        if (newUnlocks.length) showNotification('🗺️ 發現：' + newUnlocks.join('、'));
        else showNotification('已經探索過了');
        renderSidebar();
        playerTick();
      }});
    }
    if (template.type === 'character' && template.dialogue) {
      actions.push({ text: '💬 對話', fn: () => { S.dialogOpen(); window.DialogSystem.showDialogue(template.dialogue); }});
    }
    if (template.type === 'enemy') {
      actions.push({ text: '⚔️ 戰鬥（將角色拖過來）', fn: () => showNotification('將角色拖到敵人身上！')});
    }
    if (template.type === 'item' || template.type === 'resource') {
      const prices = E.getShopPrices(card.templateId);
      actions.push({ text: '💰 賣出 (' + prices.sell + '金幣)', fn: () => {
        const r = E.sellItem(card.templateId, prices.sell);
        showNotification(r.message);
        refreshAllCards();
        playerTick();
      }});
    }
    if (template.type === 'item') {
      actions.push({ text: '🎒 放入背包', fn: () => {
        E.removeFromSidebar(card.templateId);
        E.addToInventory(card.templateId);
        removeCardElement(card.id);
        refreshAllCards();
      }});
    }
    if (template.type === 'recipe') {
      actions.push({ text: '📖 查看配方', fn: () => showNotification(template.desc || template.name) });
    }

    if (actions.length === 0) {
      actions.push({ text: template.desc ? template.desc.slice(0, 40) : '無可用動作', fn: () => {} });
    }

    actions.forEach(a => {
      const btn = document.createElement('div');
      btn.className = 'context-menu-item';
      btn.textContent = a.text;
      btn.addEventListener('click', () => { a.fn(); closeContextMenu(); });
      menu.appendChild(btn);
    });

    document.body.appendChild(menu);
    activeContextMenu = menu;
  }

  // Close context menu on click elsewhere
  document.addEventListener('click', closeContextMenu);

  function onCardDblClick(e) {
    const cardId = parseInt(e.currentTarget.dataset.cardId);
    const card = E.state.boardCards.find(c => c.id === cardId);
    if (!card) return;

    const template = E.getCardTemplate(card.templateId);
    if (!template) return;

    // Character → dialogue
    if (template.type === 'character' && template.dialogue) {
      S.dialogOpen();
      window.DialogSystem.showDialogue(template.dialogue);
      playerTick();
    }
    // Location → show adjacent locations + unlock
    else if (template.type === 'location') {
      const adjacent = E.getAdjacentLocations(card.templateId);
      const locked = adjacent.filter(id => !E.state.unlockedLocations.includes(id));
      const newUnlocks = E.unlockAdjacentLocations(card.templateId);
      if (newUnlocks.length > 0) {
        showNotification(`🗺️ 發現了：${newUnlocks.join('、')}`);
        S.cardPlace();
      }
      renderSidebar();
      playerTick();
    }
    // Item with value → show buy/sell
    else if ((template.type === 'item' || template.type === 'resource') && template.value) {
      const prices = E.getShopPrices(card.templateId);
      showNotification(`${template.icon} ${template.name} | 賣出: ${prices.sell}💰 | 價值: ${template.value}g`);
    }
    // RPG item → show info
    else if (template.type === 'item' || template.type === 'resource') {
      showNotification(`${template.icon} ${template.name}: ${template.desc || ''}`);
    }
    // Recipe → show crafting info
    else if (template.type === 'recipe') {
      showNotification(`📖 ${template.name}: ${template.desc || ''}`);
    }
    // Enemy → initiate combat
    else if (template.type === 'enemy') {
      showNotification(`⚔️ 將角色拖到敵人身上進行戰鬥！`);
    }
  }

  // ═══════════════════════════════════════════════════════
  // Sidebar Rendering
  // ═══════════════════════════════════════════════════════
  function renderSidebar() {
    // Available cards
    availableCards.innerHTML = '';
    E.state.sidebarCards.forEach(sc => {
      const template = E.getCardTemplate(sc.templateId);
      if (!template) return;

      const el = document.createElement('div');
      el.className = 'sidebar-card';
      el.innerHTML = `
        <span class="sc-icon">${template.icon}</span>
        <div class="sc-info">
          <div class="sc-name">${template.name}</div>
          <div class="sc-desc">${template.desc ? template.desc.slice(0, 30) + '...' : ''}</div>
        </div>
        ${sc.count > 1 ? `<span class="sc-count">×${sc.count}</span>` : ''}
      `;

      // Drag from sidebar
      el.addEventListener('mousedown', (e) => {
        e.preventDefault();
        placeCardFromSidebar(sc.templateId, e.clientX, e.clientY);
      });

      availableCards.appendChild(el);
    });

    // Inventory
    inventoryCards.innerHTML = '';
    E.state.inventory.forEach(inv => {
      const template = E.getCardTemplate(inv.templateId);
      if (!template) return;

      const el = document.createElement('div');
      el.className = 'sidebar-card';
      el.innerHTML = `
        <span class="sc-icon">${template.icon}</span>
        <div class="sc-info">
          <div class="sc-name">${template.name}</div>
          <div class="sc-desc">${template.desc ? template.desc.slice(0, 30) + '...' : ''}</div>
        </div>
        ${inv.count > 1 ? `<span class="sc-count">×${inv.count}</span>` : ''}
      `;

      el.addEventListener('click', () => {
        placeCardFromInventory(inv.templateId);
      });

      inventoryCards.appendChild(el);
    });
  }

  function placeCardFromSidebar(templateId, x, y) {
    if (!E.removeFromSidebar(templateId)) return;

    // Place on board near click position
    const rect = board.getBoundingClientRect();
    const cardX = Math.max(10, Math.min(rect.width - 130, x - rect.left - 60));
    const cardY = Math.max(10, Math.min(rect.height - 170, y - rect.top - 80));

    const card = E.createBoardCard(templateId, cardX, cardY);
    if (card) {
      createCardElement(card);
      S.cardPlace();
    }
    renderSidebar();
  }

  function placeCardFromInventory(templateId) {
    if (!E.removeFromInventory(templateId)) return;

    const rect = board.getBoundingClientRect();
    const cardX = 50 + Math.random() * (rect.width - 200);
    const cardY = 50 + Math.random() * (rect.height - 250);

    const card = E.createBoardCard(templateId, cardX, cardY);
    if (card) {
      createCardElement(card);
      S.cardPlace();
    }
    renderSidebar();
  }

  // ═══════════════════════════════════════════════════════
  // HUD Updates
  // ═══════════════════════════════════════════════════════
  function updateHUD() {
    const s = E.state;
    const timeIcons = { morning: '🌅', afternoon: '☀️', evening: '🌇', night: '🌙' };
    const timeNames = { morning: 'Morning', afternoon: 'Afternoon', evening: 'Evening', night: 'Night' };

    dayDisplay.textContent = `📅 Day ${s.day}`;
    timeDisplay.textContent = `${timeIcons[s.timeOfDay]} ${timeNames[s.timeOfDay]}`;
    hpDisplay.textContent = `❤️ ${s.hp}`;
    sanDisplay.textContent = `🧠 ${s.sanity}`;
    goldDisplay.textContent = `💰 ${s.gold}`;

    // Equipment bonus display
    const bonus = E.getEquipmentBonus();
    if (bonus.atk > 0 || bonus.def > 0) {
      const eq = s.equipment;
      const eqText = [eq.weapon ? '⚔️' : '', eq.armor ? '🛡️' : '', eq.accessory ? '💍' : ''].filter(Boolean).join('');
      if (eqText) goldDisplay.title = `裝備: ${eqText} ATK+${bonus.atk} DEF+${bonus.def}`;
    }

    // Knowledge display
    if (s.knowledge > 0) {
      hpDisplay.title = `知識: ${s.knowledge}`;
    }

    // Color coding
    hpDisplay.style.color = s.hp < 30 ? '#f85149' : s.hp < 60 ? '#d29922' : '';
    sanDisplay.style.color = s.sanity < 30 ? '#f85149' : s.sanity < 60 ? '#d29922' : '';

    // Night background
    if (s.timeOfDay === 'night') {
      board.style.background = 'linear-gradient(180deg, #050510 0%, #0a0a1a 100%)';
    } else if (s.timeOfDay === 'evening') {
      board.style.background = 'linear-gradient(180deg, #0d0d20 0%, #101018 100%)';
    } else {
      board.style.background = '#0d1117';
    }
  }

  // ═══════════════════════════════════════════════════════
  // Tooltip
  // ═══════════════════════════════════════════════════════
  const tooltip = document.getElementById('card-tooltip');
  const tooltipName = document.getElementById('tooltip-name');
  const tooltipDesc = document.getElementById('tooltip-desc');
  const tooltipStats = document.getElementById('tooltip-stats');

  function onCardMouseEnter(e) {
    const cardId = parseInt(e.currentTarget.dataset.cardId);
    const card = E.state.boardCards.find(c => c.id === cardId);
    if (!card) return;

    const template = E.getCardTemplate(card.templateId);
    if (!template) return;

    tooltipName.textContent = `${template.icon} ${template.name}`;
    tooltipName.style.color = template.color || '#e6edf3';
    tooltipDesc.textContent = template.desc || '';

    let statsHtml = '';
    if (template.stats) {
      statsHtml = `❤️${template.stats.hp || '?'} ⚔️${template.stats.atk || '?'} 🛡️${template.stats.def || '?'} 💨${template.stats.spd || '?'}`;
    } else if (template.worldLine) {
      const wl = window.CARDS_DATA?.WORLD_LINES?.[template.worldLine];
      statsHtml = wl ? `世界線: ${wl.name}` : '';
    } else if (template.category) {
      statsHtml = `類型: ${template.category}`;
    }
    tooltipStats.textContent = statsHtml;

    const rect = e.currentTarget.getBoundingClientRect();
    tooltip.style.left = (rect.right + 10) + 'px';
    tooltip.style.top = rect.top + 'px';
    tooltip.classList.remove('hidden');
  }

  function onCardMouseLeave() {
    tooltip.classList.add('hidden');
  }

  // ═══════════════════════════════════════════════════════
  // Notification
  // ═══════════════════════════════════════════════════════
  let notifTimer = null;
  function showNotification(text) {
    notification.textContent = text;
    notification.classList.remove('hidden');
    clearTimeout(notifTimer);
    notifTimer = setTimeout(() => notification.classList.add('hidden'), 2500);
  }

  // ═══════════════════════════════════════════════════════
  // Refresh All Cards
  // ═══════════════════════════════════════════════════════
  function refreshAllCards() {
    // Remove stale elements
    cardElements.forEach((el, id) => {
      if (!E.state.boardCards.find(c => c.id === id)) {
        el.remove();
        cardElements.delete(id);
      }
    });

    // Create/update elements
    for (const card of E.state.boardCards) {
      if (!cardElements.has(card.id)) {
        createCardElement(card);
      } else {
        updateCardElement(card);
      }
    }

    renderSidebar();
    updateHUD();
  }

  // ═══════════════════════════════════════════════════════
  // Sidebar Tabs
  // ═══════════════════════════════════════════════════════
  document.querySelectorAll('.sidebar-tabs .tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.sidebar-tabs .tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(`${tab.dataset.tab}-cards`).classList.add('active');
      S.click();
    });
  });

  // ═══════════════════════════════════════════════════════
  // Settings
  // ═══════════════════════════════════════════════════════
  btnSettings.addEventListener('click', () => {
    settingsOverlay.classList.remove('hidden');
    S.click();
  });
  settingsClose.addEventListener('click', () => {
    settingsOverlay.classList.add('hidden');
    S.click();
  });
  settingVolume.addEventListener('input', (e) => {
    const v = e.target.value / 100;
    S.setVolume(v);
    E.state.volume = v;
    volumeValue.textContent = e.target.value + '%';
  });

  // ═══════════════════════════════════════════════════════
  // Controls
  // ═══════════════════════════════════════════════════════
  btnPause.addEventListener('click', () => {
    E.state.paused = !E.state.paused;
    btnPause.textContent = E.state.paused ? '▶️' : '⏸';
    btnPause.classList.toggle('active', E.state.paused);
    S.click();
  });

  btnSpeed.addEventListener('click', () => {
    E.state.speed = (E.state.speed % 3) + 1;
    const labels = { 1: '▶️', 2: '⏩', 3: '⏭️' };
    btnSpeed.textContent = labels[E.state.speed];
    S.click();
  });

  btnDraw.addEventListener('click', () => {
    const result = E.drawCard();
    if (result.success) {
      E.addToSidebar(result.templateId);
      renderSidebar();
      const template = E.getCardTemplate(result.templateId);
      showNotification(`📦 獲得 ${template?.name || result.templateId}`);
      S.collect();
      playerTick();
    } else {
      showNotification(result.message);
      S.warning();
    }
  });

  // ═══════════════════════════════════════════════════════
  // ═══════════════════════════════════════════════════════
  // Time advances only when player takes action
  // ═══════════════════════════════════════════════════════
  function playerTick() {
    const prevTime = E.state.timeOfDay;
    E.advanceTime();

    // Time transition effects
    if (E.state.timeOfDay !== prevTime) {
      if (E.state.timeOfDay === 'night') {
        S.startNightAmbience();
        showNotification('🌙 夜晚降臨...');
      } else if (prevTime === 'night') {
        S.stopNightAmbience();
        S.dayTransition();
        showNotification(`🌅 新的一天！Day ${E.state.day}`);
      } else if (E.state.timeOfDay === 'evening') {
        showNotification('🌇 傍晚...');
      }
    }

    refreshAllCards();
    E.autoSave();
  }

  // ═══════════════════════════════════════════════════════
  // Initialize
  // ═══════════════════════════════════════════════════════
  async function init() {
    S.init();

    // Try to load electron settings
    if (window.electronAPI) {
      window.electronAPI.getSettings().then(settings => {
        E.state.volume = settings.volume;
        S.setVolume(settings.volume);
        E.state.language = settings.language;
        E.state.quality = settings.quality;
        E.state.showTutorial = settings.showTutorial;
      });
    }

    // Try connecting to Angela AI backend
    if (window.angelaAPI) {
      const connected = await window.angelaAPI.connect();
      if (connected) {
        showNotification('🤖 已連接到 Angela AI');
      }
    }

    // Try loading saved game, otherwise start new
    if (!E.loadGame()) {
      E.initNewGame();
    }
    refreshAllCards();

    // Time advances on player actions (no auto-timer)

    // Show tutorial dialog
    if (E.state.showTutorial) {
      setTimeout(() => {
        window.DialogSystem.showDialogue('tutorial_start');
      }, 500);
    }
  }

  // Expose for dialog system
  window.Renderer = {
    refreshAllCards,
    showNotification,
    updateHUD,
    renderSidebar,
    playerTick,
  };

  // Start when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose CARDS data for tooltip — preserve full object including NPC_SCHEDULES
  if (window.CARDS_DATA) {
    window.CARDS_DATA.CARDS = CARDS;
    window.CARDS_DATA.WORLD_LINES = WORLD_LINES;
  } else {
    window.CARDS_DATA = { CARDS, WORLD_LINES };
  }
})();
