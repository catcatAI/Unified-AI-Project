/**
 * crystal-cards game-engine 純函數層行為測試（node:test）。
 *
 * WHY（P1-10）：crystal-cards 此前零行為測試（只有 import/檔案完整性層）。
 * 本檔以 node:vm 模擬瀏覽器經典 <script> 語意——cards.js 與 game-engine.js
 * 在同一 vm context 的兩次 runInContext 共享頂層詞法環境（CARDS 全域可見），
 * 與 bot-player.js 的雙 eval 寫法不同（該寫法第二次 eval 看不到 cards 的
 * const，載入即 ReferenceError，已另修）。
 *
 * 執行：node --test tests/frontend/test_crystal_engine.mjs
 * （pytest 橋：tests/frontend/test_crystal_engine_node.py）
 */
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import vm from 'node:vm'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..')
const CC = path.join(ROOT, 'apps', 'crystal-cards')

function loadEngine() {
  const store = new Map()
  const sandbox = {
    console,
    window: {},
    document: {
      readyState: 'complete',
      getElementById: () => ({
        addEventListener() {},
        classList: { add() {}, remove() {} },
        innerHTML: '',
        textContent: '',
        style: {},
        appendChild() {},
        querySelectorAll: () => [],
      }),
      querySelectorAll: () => [],
      addEventListener() {},
    },
    localStorage: {
      getItem: (k) => (store.has(k) ? store.get(k) : null),
      setItem: (k, v) => store.set(k, String(v)),
      removeItem: (k) => store.delete(k),
    },
    requestAnimationFrame: () => {},
    setTimeout: () => 0,
    clearTimeout: () => {},
  }
  const ctx = vm.createContext(sandbox)
  const cardsRaw = fs.readFileSync(path.join(CC, 'game-data', 'cards.js'), 'utf8')
  vm.runInContext(
    cardsRaw.replace(/if \(typeof module[\s\S]*$/, '') +
      '\nwindow.CARDS_DATA = { CARDS, WORLD_LINES, NPC_SCHEDULES };',
    ctx
  )
  vm.runInContext(fs.readFileSync(path.join(CC, 'src', 'game-engine.js'), 'utf8'), ctx)
  assert.ok(ctx.window.GameEngine, 'engine must export window.GameEngine')
  return { E: ctx.window.GameEngine, store, ctx }
}

test('harness loads engine with P1-10 target exports', () => {
  const { E, ctx } = loadEngine()
  for (const fn of ['tryStack', 'executeCombat', 'saveGame', 'loadGame']) {
    assert.equal(typeof E[fn], 'function', `${fn} must be exported`)
  }
  assert.ok(Array.isArray(E.state.recipes) && E.state.recipes.length > 0)
  const cards = ctx.window.CARDS_DATA.CARDS
  assert.ok(Object.keys(cards).length > 0, 'CARDS must be populated')
})

test('initNewGame seeds a playable state', () => {
  const { E } = loadEngine()
  const s = E.initNewGame()
  assert.equal(s.hp, 100)
  // 注意：vm 跨 realm 物件不能與 host 字面量 deepStrictEqual（原型不同）——逐欄比對
  assert.equal(s.equipment.weapon, null)
  assert.equal(s.equipment.armor, null)
  assert.equal(s.equipment.accessory, null)
  assert.ok(s.sidebarCards.length >= 5, 'starting sidebar cards')
  assert.ok(s.boardCards.length >= 2, 'starting characters on board')
})

test('tryStack merges identical resources up to maxStack', () => {
  const { E } = loadEngine()
  const a = E.createBoardCard('res_wood', 10, 10)
  const b = E.createBoardCard('res_wood', 40, 40)
  a.count = 15
  b.count = 10
  const r = E.tryStack(a, b)
  assert.equal(r.type, 'stack')
  assert.equal(b.count, 20, 'capped at res_wood maxStack=20')
  assert.equal(
    E.state.boardCards.find((c) => c.id === a.id),
    undefined,
    'dragged removed'
  )
  assert.ok(
    E.state.boardCards.some((c) => c.id === b.id),
    'target survives'
  )
})

test('tryStack: unknown template and non-craftable pair return null', () => {
  const { E } = loadEngine()
  const wood = E.createBoardCard('res_wood', 0, 0)
  const ghost = { id: 999, templateId: 'no_such_template', count: 1, x: 0, y: 0 }
  assert.equal(E.tryStack(ghost, wood), null)

  const w2 = E.createBoardCard('res_wood', 0, 0)
  const stone = E.createBoardCard('res_stone', 0, 0)
  assert.equal(E.tryStack(w2, stone), null, 'wood+stone has no recipe')
})

test('tryStack crafts legacy recipe: res_iron + res_wood -> item_knife', () => {
  const { E } = loadEngine()
  const iron = E.createBoardCard('res_iron', 0, 0)
  const wood = E.createBoardCard('res_wood', 0, 0)
  const r = E.tryStack(iron, wood)
  assert.equal(r.type, 'craft')
  assert.match(r.message, /小刀/)
  assert.equal(E.state.boardCards.length, 0, 'both ingredients consumed off board')
  const inv = E.state.inventory.find((i) => i.templateId === 'item_knife')
  assert.ok(inv, 'item_knife must land in inventory')
  assert.equal(inv.count, 1)
})

test('tryStack crafts quantity-aware recipe: 草藥×2+火元素×1 -> board card', () => {
  const { E } = loadEngine()
  const herb = E.createBoardCard('rpg_item_草藥', 5, 5)
  const fire = E.createBoardCard('rpg_item_火元素', 50, 50)
  herb.count = 2
  fire.count = 1
  const r = E.tryStack(herb, fire)
  assert.equal(r.type, 'craft')
  assert.ok(r.card, 'output card created on board')
  assert.equal(r.card.templateId, 'rpg_item_火焰藥水')
  assert.equal(
    E.state.boardCards.some((c) => c.id === herb.id),
    false,
    'herb consumed'
  )
  assert.equal(
    E.state.boardCards.some((c) => c.id === fire.id),
    false,
    'fire consumed'
  )
})

test('tryStack: character + matching location yields dialogue trigger', () => {
  const { E } = loadEngine()
  const ch = E.createBoardCard('char_hikuraya', 0, 0)
  const loc = E.createBoardCard('loc_library', 0, 0)
  const r = E.tryStack(ch, loc)
  assert.equal(r.type, 'dialogue')
  assert.equal(r.dialogueId, 'greeting_hikuraya')
  assert.equal(r.character.id, 'char_hikuraya')
})

test('executeCombat kills defender, removes it, deposits loot', () => {
  const { E } = loadEngine()
  E.initNewGame()
  const defenderTemplate = E.getCardTemplate('enemy_shadow')
  const attackerTemplate = { name: '測試勇者', stats: { hp: 999, atk: 500, def: 100, spd: 10 } }
  const defenderCard = E.createBoardCard('enemy_shadow', 100, 100)
  const r = E.executeCombat(attackerTemplate, defenderTemplate, {}, defenderCard)
  assert.equal(r.won, true)
  assert.ok(r.results.some((x) => x.text.includes('被擊敗')))
  assert.equal(
    E.state.boardCards.some((c) => c.id === defenderCard.id),
    false
  )
  // enemy_shadow.loot = [res_crystal_shard]（resource → inventory）
  const loot = E.state.inventory.find((i) => i.templateId === 'res_crystal_shard')
  assert.ok(loot && loot.count >= 1, 'loot deposited')
  assert.equal(E.state.hp, 100, 'defender died before counter-attack')
})

test('executeCombat: counter-damage can end the game', () => {
  const { E } = loadEngine()
  E.initNewGame()
  E.state.hp = 1
  const defenderTemplate = E.getCardTemplate('rpg_enemy_雷靈') // atk 35
  const defenderCard = E.createBoardCard('rpg_enemy_雷靈', 10, 10)
  // attackerTemplate=null → 引擎預設 atk8：斬不死 hp40 的守衛 → 反擊 ≥34 → hp 1→0
  const r = E.executeCombat(null, defenderTemplate, {}, defenderCard)
  assert.equal(r.gameOver, true)
  assert.equal(E.state.hp, 0)
  assert.ok(r.results.some((x) => x.text.includes('你倒下了')))
})

test('saveGame/loadGame roundtrip restores state and rebuilds board ids', () => {
  const { E, store } = loadEngine()
  E.initNewGame()
  E.createBoardCard('res_wood', 123, 456)
  E.state.hp = 57
  E.state.gold = 999
  E.state.day = 42
  E.state.inventory.push({ templateId: 'res_herb', count: 3 })
  assert.equal(E.saveGame(), true)
  assert.ok(store.has('crystal-cards-save'))
  const savedTemplateIds = E.state.boardCards.map((c) => c.templateId)

  // wreck everything
  E.state.hp = 1
  E.state.gold = 0
  E.state.boardCards = []
  E.state.inventory = []

  assert.equal(E.loadGame(), true)
  assert.equal(E.state.hp, 57)
  assert.equal(E.state.gold, 999)
  assert.equal(E.state.day, 42)
  const herb = E.state.inventory.find((i) => i.templateId === 'res_herb')
  assert.ok(herb && herb.count === 3, 'inventory restored')
  assert.deepEqual(
    E.state.boardCards.map((c) => c.templateId),
    savedTemplateIds,
    'board card order/content restored'
  )
  assert.deepEqual(
    E.state.boardCards.map((c) => c.id),
    E.state.boardCards.map((_, i) => i + 1),
    'ids reassigned sequentially from 1'
  )
  assert.ok(
    E.state.boardCards.every((c) => c.count === 1 && c.stackId === null),
    'load forces count=1, stackId=null (documented contract)'
  )
})

test('loadGame rejects invalid payloads and clears the key', () => {
  const { E, store } = loadEngine()
  assert.equal(E.loadGame(), false, 'no save key')

  store.set('crystal-cards-save', '{"broken":true}')
  assert.equal(E.loadGame(), false, 'missing hp/boardCards')
  assert.equal(store.has('crystal-cards-save'), false, 'invalid save cleared')

  store.set('crystal-cards-save', '{"hp":"not-a-number","boardCards":[]}')
  assert.equal(E.loadGame(), false, 'wrong hp type')
  assert.equal(store.has('crystal-cards-save'), false, 'invalid save cleared')
})
