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
    hasMoved: false,  // distinguish click from drag
  };

  // ── Board bounds helper ──
  function clampToBoard(x, y) {
    const rect = board.getBoundingClientRect();
    const cardW = 120, cardH = 160;
    return {
      x: Math.max(0, Math.min(rect.width - cardW, x)),
      y: Math.max(0, Math.min(rect.height - cardH, y)),
    };
  }

  function clientToBoard(clientX, clientY) {
    const rect = board.getBoundingClientRect();
    return { x: clientX - rect.left, y: clientY - rect.top };
  }

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
      <div class="card-subtitle">${template.type === 'character' ? (template.role || '') : (template.category || template.itemType || '')}</div>
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

    // Calculate offset relative to board, not viewport
    const boardPos = clientToBoard(e.clientX, e.clientY);
    dragState.active = true;
    dragState.cardId = cardId;
    dragState.offsetX = boardPos.x - card.x;
    dragState.offsetY = boardPos.y - card.y;
    dragState.startX = card.x;
    dragState.startY = card.y;
    dragState.hasMoved = false;

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

    const boardPos = clientToBoard(e.clientX, e.clientY);
    let newX = boardPos.x - dragState.offsetX;
    let newY = boardPos.y - dragState.offsetY;

    // Clamp to board bounds — prevent dragging off-screen
    const clamped = clampToBoard(newX, newY);
    card.x = clamped.x;
    card.y = clamped.y;

    dragState.hasMoved = true;

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
      board.classList.add('stack-mode');
    } else {
      board.classList.remove('stack-mode');
    }

    // Show boundary glow when card is near edge
    const boardRect = board.getBoundingClientRect();
    const edgeThreshold = 30;
    const nearEdge = card.x < edgeThreshold || card.y < edgeThreshold ||
      card.x > boardRect.width - 120 - edgeThreshold ||
      card.y > boardRect.height - 160 - edgeThreshold;
    if (nearEdge) {
      board.classList.add('drag-boundary');
    } else {
      board.classList.remove('drag-boundary');
    }
  }

  function onDragEnd(e) {
    document.removeEventListener('mousemove', onDragMove);
    document.removeEventListener('mouseup', onDragEnd);

    if (!dragState.active) return;

    const card = E.state.boardCards.find(c => c.id === dragState.cardId);
    const wasDrag = dragState.hasMoved;

    const el = cardElements.get(dragState.cardId);
    if (el) {
      el.classList.remove('dragging');
      el.style.zIndex = '';
    }

    // Remove stack target highlights
    cardElements.forEach((el) => el.classList.remove('stack-target'));
    board.classList.remove('stack-mode');

    // If card was not moved (just a click), don't try stacking
    if (wasDrag && card) {
      // Ensure final position is within bounds
      const clamped = clampToBoard(card.x, card.y);
      card.x = clamped.x;
      card.y = clamped.y;
      if (el) {
        el.style.left = card.x + 'px';
        el.style.top = card.y + 'px';
      }

      // Check for stacking
      const target = E.findStackAt(card.x, card.y, card.id);
      if (target) {
        const result = E.tryStack(card, target);
        if (result) {
          handleStackResult(result, target);
        }
      }

      S.cardPlace();
    }

    board.classList.remove('drag-boundary');
    dragState.active = false;
    dragState.cardId = null;
    dragState.hasMoved = false;
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
    // Clamp menu position to screen bounds
    const menuW = 220, menuH = 200;
    const mx = Math.min(e.clientX, window.innerWidth - menuW - 8);
    const my = Math.min(e.clientY, window.innerHeight - menuH - 8);
    menu.style.left = Math.max(8, mx) + 'px';
    menu.style.top = Math.max(8, my) + 'px';

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
        E.removeBoardCard(card.id);
        E.state.gold += prices.sell;
        removeCardElement(card.id);
        showNotification(`💰 賣出 ${template.name}，獲得 ${prices.sell} 金幣`);
        refreshAllCards();
        playerTick();
      }});
    }
    if (template.type === 'item' || template.type === 'resource') {
      actions.push({ text: '🎒 收回側邊欄', fn: () => {
        E.addToSidebar(card.templateId);
        E.removeBoardCard(card.id);
        removeCardElement(card.id);
        refreshAllCards();
        showNotification(`${template.name} 已收回側邊欄`);
      }});
    }
    if (template.type === 'item' && ((template.category || template.itemType) === 'weapon' || (template.stats && (template.stats.atk || template.stats.def)))) {
      const slot = (template.stats?.atk || 0) > (template.stats?.def || 0) ? 'weapon' : 'armor';
      actions.push({ text: `🗡️ 裝備到${slot === 'weapon' ? '武器' : '防具'}欄`, fn: () => {
        const result = E.equipItem(card.id, slot);
        if (result.success) {
          removeCardElement(card.id);
          showNotification(result.message);
          refreshAllCards();
        } else {
          showNotification(result.message || '裝備失敗');
        }
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

  // Close context menu on click elsewhere or Escape
  document.addEventListener('click', closeContextMenu);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeContextMenu();
  });

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
      // Special location story triggers
      if (card.templateId === 'loc_corridor' && !E.state.flags.corridor_visited) {
        E.state.flags.corridor_visited = true;
        S.dialogOpen();
        window.DialogSystem.showDialogue('corridor_start');
        playerTick();
        return;
      }
      const newUnlocks = E.unlockAdjacentLocations(card.templateId);
      if (newUnlocks.length > 0) {
        showNotification(`🗺️ 發現了：${newUnlocks.join('、')}`);
        S.cardPlace();
      } else {
        const adjacent = E.getAdjacentLocations(card.templateId);
        const locked = adjacent.filter(id => !E.state.unlockedLocations.includes(id));
        if (locked.length > 0) {
          showNotification(`🔒 未探索: ${locked.map(id => {
            const t = E.getCardTemplate(id);
            return t?.name || id;
          }).join('、')}`);
        } else {
          showNotification('🗺️ 所有鄰近地點已解鎖');
        }
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
    // Enemy → show enemy info
    else if (template.type === 'enemy') {
      const stats = template.stats;
      showNotification(`${template.icon} ${template.name} | HP:${stats?.hp || '?'} ATK:${stats?.atk || '?'} DEF:${stats?.def || '?'}`);
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
      `;      // Click to place from sidebar
      el.addEventListener('click', (e) => {
        e.preventDefault();
        placeCardFromSidebar(sc.templateId);
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

  function placeCardFromSidebar(templateId) {
    if (!E.removeFromSidebar(templateId)) return;

    // Always place in visible center area of the board
    const rect = board.getBoundingClientRect();
    const centerX = rect.width / 2 - 60;
    const centerY = rect.height / 2 - 80;
    // Add slight randomness so stacked cards don't overlap exactly
    const jitterX = (Math.random() - 0.5) * 160;
    const jitterY = (Math.random() - 0.5) * 120;
    const pos = clampToBoard(centerX + jitterX, centerY + jitterY);

    const card = E.createBoardCard(templateId, pos.x, pos.y);
    if (card) {
      const el = createCardElement(card);
      if (el) el.classList.add('resource-spawn');
      S.cardPlace();
    }
    renderSidebar();
  }

  function placeCardFromInventory(templateId) {
    if (!E.removeFromInventory(templateId)) return;

    // Place near center of board with slight randomness
    const rect = board.getBoundingClientRect();
    const pos = clampToBoard(
      rect.width / 2 - 60 + (Math.random() - 0.5) * 200,
      rect.height / 2 - 80 + (Math.random() - 0.5) * 150
    );

    const card = E.createBoardCard(templateId, pos.x, pos.y);
    if (card) {
      const el = createCardElement(card);
      if (el) el.classList.add('resource-spawn');
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

    // Equipment section
    const eqSection = document.getElementById('equipment-section');
    if (eqSection) {
      const eq = s.equipment;
      const bonus = E.getEquipmentBonus();
      const slots = [
        { key: 'weapon', icon: '⚔️', label: '武器' },
        { key: 'armor', icon: '🛡️', label: '防具' },
        { key: 'accessory', icon: '💍', label: '飾品' },
      ];
      let html = '<div class="eq-title">裝備欄</div>';
      let hasEquip = false;
      for (const slot of slots) {
        const tid = eq[slot.key];
        if (tid) {
          const t = E.getCardTemplate(tid);
          hasEquip = true;
          html += `<div class="eq-slot" title="點擊卸下"><span class="eq-icon">${slot.icon}</span> <span class="eq-name">${t?.name || tid}</span> <button class="eq-unequip" data-slot="${slot.key}">✕</button></div>`;
        }
      }
      if (hasEquip) {
        html += `<div class="eq-bonus">ATK+${bonus.atk} DEF+${bonus.def}</div>`;
      } else {
        html += '<div class="eq-empty">無裝備</div>';
      }
      eqSection.innerHTML = html;
      // Wire unequip buttons
      eqSection.querySelectorAll('.eq-unequip').forEach(btn => {
        btn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          const slot = btn.dataset.slot;
          const result = E.unequipItem(slot);
          if (result.success) {
            showNotification(result.message);
            refreshAllCards();
          }
        });
      });
    }

    // Knowledge display
    if (s.knowledge > 0) {
      hpDisplay.title = `知識: ${s.knowledge}`;
    }

    // Update draw cost display
    const drawCost = 3 + Math.floor(s.day / 3);
    if (drawCostValue) drawCostValue.textContent = drawCost;

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
    } else if (template.category || template.itemType) {
      statsHtml = `類型: ${template.category || template.itemType}`;
    }
    tooltipStats.textContent = statsHtml;

    const rect = e.currentTarget.getBoundingClientRect();
    // Clamp tooltip to screen bounds
    let tx = rect.right + 10;
    let ty = rect.top;
    if (tx + 250 > window.innerWidth) tx = rect.left - 260;
    if (ty + 100 > window.innerHeight) ty = window.innerHeight - 110;
    tooltip.style.left = Math.max(4, tx) + 'px';
    tooltip.style.top = Math.max(4, ty) + 'px';
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
  // Pause: freezes enemy spawning and sanity drain
  btnPause.addEventListener('click', () => {
    E.state.paused = !E.state.paused;
    btnPause.textContent = E.state.paused ? '▶️' : '⏸';
    btnPause.classList.toggle('active', E.state.paused);
    showNotification(E.state.paused ? '⏸ 遊戲暫停（敵人不會出現）' : '▶️ 遊戲繼續');
    S.click();
  });

  // Speed button → New Game (since time is action-based)
  btnSpeed.addEventListener('click', () => {
    if (confirm('開始新遊戲？存檔會被覆蓋。')) {
      E.initNewGame();
      refreshAllCards();
      showNotification('🆕 新遊戲開始！');
      S.craft();
    }
    S.click();
  });
  btnSpeed.textContent = '🆕';
  btnSpeed.title = '新遊戲';

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
  const npcSchedules = window.CARDS_DATA?.NPC_SCHEDULES || (typeof NPC_SCHEDULES !== 'undefined' ? NPC_SCHEDULES : {});
  window.CARDS_DATA = { CARDS, WORLD_LINES, NPC_SCHEDULES: npcSchedules };
})();
