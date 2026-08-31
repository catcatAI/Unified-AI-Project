/**
 * dialog.js — Dialogue and story system
 * Shows dialog boxes with choices and applies game effects
 */

(function () {
  const E = window.GameEngine;
  const S = window.sounds;

  const overlay = document.getElementById('dialog-overlay');
  const speakerEl = document.getElementById('dialog-speaker');
  const textEl = document.getElementById('dialog-text');
  const choicesEl = document.getElementById('dialog-choices');

  let currentDialogueId = null;

  function showDialogue(dialogueId) {
    const { CARDS } = window.CARDS_DATA || {};
    if (!CARDS) return;

    const dialogue = CARDS.dialogues[dialogueId];
    if (!dialogue) {
      console.warn('Dialogue not found:', dialogueId);
      return;
    }

    currentDialogueId = dialogueId;

    // Set speaker
    speakerEl.textContent = dialogue.speaker || '???';

    // Typewriter effect for text
    textEl.textContent = '';
    typeWriter(dialogue.text, textEl, 30);

    // Render choices
    choicesEl.innerHTML = '';

    setTimeout(() => {
      dialogue.choices.forEach((choice, idx) => {
        const btn = document.createElement('button');
        btn.className = 'dialog-choice';

        // Check requirements
        let available = true;
        let reqText = '';

        if (choice.requires) {
          if (choice.requires.knowledge && E.state.knowledge < choice.requires.knowledge) {
            available = false;
            reqText = `需要知識 ${choice.requires.knowledge}`;
          }
          if (choice.requires.item && !E.hasItem(choice.requires.item)) {
            available = false;
            const itemTemplate = E.getCardTemplate(choice.requires.item);
            reqText = `需要道具: ${itemTemplate?.name || choice.requires.item}`;
          }
          if (choice.requires.bond) {
            for (const [npcId, minValue] of Object.entries(choice.requires.bond)) {
              if ((E.state.bonds[npcId] || 0) < minValue) {
                available = false;
                reqText = `需要好感度`;
              }
            }
          }
        }

        if (!available) {
          btn.classList.add('disabled');
        }

        btn.innerHTML = `
          ${choice.text}
          ${reqText ? `<div class="choice-req">🔒 ${reqText}</div>` : ''}
        `;

        if (available) {
          btn.addEventListener('click', () => {
            S.click();
            handleChoice(choice);
          });
        }

        choicesEl.appendChild(btn);
      });
    }, Math.min(dialogue.text.length * 30, 1500)); // Wait for typewriter

    overlay.classList.remove('hidden');
  }

  async function handleChoice(choice) {
    // Apply effects
    if (choice.effect) {
      applyEffects(choice.effect);
    }

    // Skill check
    if (choice.skillCheck) {
      const roll = Math.floor(Math.random() * 100) + 1 + E.state.knowledge / 2;
      if (roll < choice.skillCheck) {
        // Failed
        window.Renderer.showNotification('❌ 技能檢定失敗...');
        E.state.sanity = Math.max(0, E.state.sanity - 5);
      }
    }

    // Navigate to next dialogue
    if (choice.next === 'restart') {
      closeDialog();
      E.initNewGame();
      window.Renderer.refreshAllCards();
      setTimeout(() => showDialogue('tutorial_start'), 500);
      return;
    }

    if (choice.next) {
      // Try Angela AI for dynamic responses on free-text choices
      const dialogue = CARDS.dialogues[choice.next];
      if (!dialogue && window.angelaAPI?.connected) {
        const speaker = currentDialogueId ? CARDS.dialogues[currentDialogueId]?.speaker : '旁白';
        const result = await window.angelaAPI.generateNPCDialogue(speaker, choice.text);
        if (result.text) {
          showFreeDialogue(speaker, result.text, choice.next);
          return;
        }
      }
      showDialogue(choice.next);
    } else {
      // If connected to Angela, generate a continuation response
      if (window.angelaAPI?.connected && currentDialogueId) {
        const dialogue = CARDS.dialogues[currentDialogueId];
        if (dialogue?.speaker && dialogue.speaker !== '旁白') {
          const result = await window.angelaAPI.generateNPCDialogue(dialogue.speaker, choice.text);
          if (result.text && result.source === 'angela') {
            showFreeDialogue(dialogue.speaker, result.text);
            return;
          }
        }
      }
      closeDialog();
    }
  }

  // Show a dynamically generated (non-template) dialogue
  function showFreeDialogue(speaker, text, nextId) {
    speakerEl.textContent = speaker;
    textEl.textContent = '';
    typeWriter(text, textEl, 30);
    choicesEl.innerHTML = '';

    setTimeout(() => {
      const continueBtn = document.createElement('button');
      continueBtn.className = 'dialog-choice';
      continueBtn.textContent = '繼續';
      continueBtn.addEventListener('click', () => {
        S.click();
        if (nextId) {
          showDialogue(nextId);
        } else {
          closeDialog();
        }
      });
      choicesEl.appendChild(continueBtn);
    }, Math.min(text.length * 30, 1000));

    overlay.classList.remove('hidden');
  }

  function applyEffects(effects) {
    if (effects.hp) {
      E.state.hp = Math.max(0, Math.min(E.state.maxHp, E.state.hp + effects.hp));
    }
    if (effects.sanity) {
      E.state.sanity = Math.max(0, Math.min(100, E.state.sanity + effects.sanity));
    }
    if (effects.knowledge) {
      E.state.knowledge = Math.min(100, E.state.knowledge + effects.knowledge);
      window.Renderer.showNotification(`📖 知識 +${effects.knowledge}`);
    }
    if (effects.gold) {
      E.state.gold += effects.gold;
    }
    if (effects.items) {
      effects.items.forEach(itemId => {
        E.addToInventory(itemId);
        const template = E.getCardTemplate(itemId);
        window.Renderer.showNotification(`📦 獲得 ${template?.name || itemId}`);
      });
    }
    // Handle single unlock
    if (effects.unlock) {
      if (effects.unlock.startsWith('loc_')) {
        if (!E.state.unlockedLocations.includes(effects.unlock)) {
          E.state.unlockedLocations.push(effects.unlock);
          const template = E.getCardTemplate(effects.unlock);
          E.addToSidebar(effects.unlock);
          window.Renderer.showNotification(`🗺️ 解鎖 ${template?.name || effects.unlock}`);
          window.Renderer.renderSidebar();
        }
      } else {
        E.state.flags[effects.unlock] = true;
      }
    }
    // Handle unlocks array
    if (effects.unlocks) {
      for (const unlockId of effects.unlocks) {
        if (unlockId.startsWith('loc_')) {
          if (!E.state.unlockedLocations.includes(unlockId)) {
            E.state.unlockedLocations.push(unlockId);
            const template = E.getCardTemplate(unlockId);
            E.addToSidebar(unlockId);
            window.Renderer.showNotification(`🗺️ 解鎖 ${template?.name || unlockId}`);
            window.Renderer.renderSidebar();
          }
        } else {
          E.state.flags[unlockId] = true;
        }
      }
    }
    if (effects.bond) {
      for (const [npcId, delta] of Object.entries(effects.bond)) {
        E.state.bonds[npcId] = Math.max(0, Math.min(100, (E.state.bonds[npcId] || 50) + delta));
      }
    }

    window.Renderer.updateHUD();
  }

  function closeDialog() {
    overlay.classList.add('hidden');
    currentDialogueId = null;
  }

  // Close on clicking overlay background (only for non-required dialogues)
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay && !overlay.classList.contains('hidden')) {
      closeDialog();
    }
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (!overlay.classList.contains('hidden')) {
      const keyNum = parseInt(e.key);
      if (keyNum >= 1 && keyNum <= 9) {
        const choices = choicesEl.querySelectorAll('.dialog-choice:not(.disabled)');
        if (choices[keyNum - 1]) {
          choices[keyNum - 1].click();
        }
      }
      if (e.key === 'Escape') {
        closeDialog();
      }
    }
  });

  // ── Typewriter Effect ──
  function typeWriter(text, element, speed) {
    let i = 0;
    element.textContent = '';

    function type() {
      if (i < text.length) {
        element.textContent += text.charAt(i);
        i++;
        setTimeout(type, speed);
      }
    }
    type();
  }

  // Expose
  window.DialogSystem = {
    showDialogue,
    closeDialog,
    applyEffects,
  };
})();
