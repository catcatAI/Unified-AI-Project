#!/usr/bin/env node
/**
 * check_crystal_links.js — crystal-cards 內部 id 連結稽核
 *
 * FAIL（消費方連結，斷了就是執行期壞功能）：
 *   - dialogues[*].choices[].next → dialogues 鍵（'restart' 是 dialog.js:111
 *     特殊哨兵，觸發 initNewGame，不算斷鏈）
 *   - characters[*].dialogue → dialogues 鍵（game-engine 拖拽/點擊/觸發皆會開）
 *   - storyEvents[*].dialogue → dialogues 鍵（renderer「📖 觸發事件」會開；
 *     缺失時 dialog.js 只 console.warn，故事事件靜默失效）
 *
 * WARN（無消費方的資料欄位，僅提醒勿接線後踩雷）：
 *   - locations[*].storyNodes → storyEvents id（全倉無 storyNodes 消費者）
 *   - characters[*].location → locations id（欄位僅資料層存在，src 未消費）
 *
 * 用法：node scripts/check_crystal_links.js
 * 退出碼：有 FAIL → 1；僅 WARN/全綠 → 0
 */
'use strict'

const path = require('path')
const { CARDS } = require(path.join(
  __dirname,
  '..',
  'apps',
  'crystal-cards',
  'game-data',
  'cards.js'
))

const SENTINELS = new Set(['restart'])

function main() {
  const dialogues = CARDS.dialogues || {}
  const dialogueIds = new Set(Object.keys(dialogues))
  const storyIds = new Set((CARDS.storyEvents || []).map((e) => e.id))
  const locationIds = new Set((CARDS.locations || []).map((l) => l.id))
  const fails = []
  const warns = []

  // 1) dialogue choice chains
  let nextRefs = 0
  for (const [id, node] of Object.entries(dialogues)) {
    for (const choice of node.choices || []) {
      if (!choice.next) continue
      nextRefs += 1
      if (SENTINELS.has(choice.next)) continue
      if (!dialogueIds.has(choice.next)) {
        fails.push(`dialogues[${id}].next → '${choice.next}' 不存在`)
      }
    }
  }

  // 2) characters → dialogues
  let charRefs = 0
  for (const c of CARDS.characters || []) {
    if (!c.dialogue) continue
    charRefs += 1
    if (!dialogueIds.has(c.dialogue)) {
      fails.push(`characters[${c.id}].dialogue → '${c.dialogue}' 不存在`)
    }
    if (c.location && !locationIds.has(c.location)) {
      warns.push(`characters[${c.id}].location → '${c.location}' 不存在（unconsumed 欄位）`)
    }
  }

  // 3) storyEvents → dialogues（消費方：renderer.js 觸發事件按鈕）
  let storyRefs = 0
  for (const e of CARDS.storyEvents || []) {
    if (!e.dialogue) continue
    storyRefs += 1
    if (!dialogueIds.has(e.dialogue)) {
      fails.push(`storyEvents[${e.id}].dialogue → '${e.dialogue}' 不存在（觸發事件將靜默失效）`)
    }
  }

  // 4) storyNodes → storyEvents（unconsumed 欄位 → WARN）
  let nodeRefs = 0
  for (const loc of CARDS.locations || []) {
    for (const nid of loc.storyNodes || []) {
      nodeRefs += 1
      if (!storyIds.has(nid)) {
        warns.push(`locations[${loc.id}].storyNodes → '${nid}' 不存在（unconsumed 欄位）`)
      }
    }
  }

  const stats = [
    `dialogue keys: ${dialogueIds.size}`,
    `choices.next refs: ${nextRefs}`,
    `characters.dialogue refs: ${charRefs}`,
    `storyEvents.dialogue refs: ${storyRefs}`,
    `storyNodes refs: ${nodeRefs}`,
  ]
  console.log(stats.join('\n'))

  for (const w of warns) console.log(`WARN  ${w}`)
  for (const f of fails) console.error(`FAIL  ${f}`)

  console.log(
    `\nresult: ${fails.length} fail, ${warns.length} warn — ` +
      (fails.length ? 'BROKEN' : 'consumed links OK')
  )
  if (fails.length) process.exit(1)
}

main()
