/**
 * UnifiedShell — switchable single-frontend shell for Angela AI.
 *
 * Piles the separate UIs (pet / chat / system / multimodal / game / settings)
 * into ONE page whose panels are switched by the top nav. Everything talks to
 * the real backend via shared-js clients (AngelaAPIClient / BackendWebSocket /
 * MultimodalAPIClient) — no mock data.
 *
 * Class-toggle panel switching (modeled on the desktop settings sidebar +
 * multimodal tab pattern); game panel drives the headless GameEngine REST API
 * (POST /api/v1/game/*) so the CLI RPG is playable from the web frontend.
 *
 * ANGELA-MATRIX: [L3] [αβγδ] [B] [L2]
 */

class UnifiedShell {
  constructor() {
    this.baseURL = localStorage.getItem('backend_ip') || 'http://localhost:8000'
    this.apiBase = `${this.baseURL}/api/v1`
    this.apiClient = null
    this.multimodal = null
    this.gameSessionId = null
    this.activePanel = 'pet'
    this._multimodalWired = false
    this._monitors = []
  }

  async init() {
    this._bindNav()
    this._wireChat()
    this._wireSystem()
    this._wireMultimodal()
    this._wireGame()
    this._wireSettings()
    this._refreshBackendState()
    setInterval(() => this._refreshBackendState(), 15000)
  }

  // ========== Panel switching ==========

  _bindNav() {
    const nav = document.getElementById('unified-nav')
    if (!nav) return
    nav.querySelectorAll('button[data-panel]').forEach((btn) => {
      btn.addEventListener('click', () => this.switchPanel(btn.dataset.panel))
    })
  }

  switchPanel(name) {
    this.activePanel = name
    document
      .querySelectorAll('#unified-nav button[data-panel]')
      .forEach((b) => b.classList.toggle('active', b.dataset.panel === name))
    document
      .querySelectorAll('.shell-panel')
      .forEach((p) => p.classList.toggle('active', p.id === `panel-${name}`))
  }

  // ========== Backend status pill ==========

  async _refreshBackendState() {
    const pill = document.getElementById('unified-backend-state')
    const ipEl = document.getElementById('settings-current-ip')
    if (ipEl) ipEl.textContent = this.baseURL
    if (!pill) return
    try {
      const res = await fetch(`${this.baseURL}/api/v1/ops/status`, {
        signal: AbortSignal.timeout(5000),
      })
      const ok = res.ok
      pill.textContent = ok ? 'Online' : 'Offline'
      pill.classList.toggle('ok', ok)
    } catch (err) {
      pill.textContent = 'Offline'
      pill.classList.remove('ok')
    }
  }

  // ========== Chat (REST, real backend) ==========

  _wireChat() {
    document.getElementById('btn-chat-send').addEventListener('click', () => this._sendChat())
    document.getElementById('chat-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this._sendChat()
    })
    if (window.AngelaAPIClient) {
      try {
        this.apiClient = new AngelaAPIClient(this.baseURL)
      } catch (err) {
        console.warn('[UnifiedShell] AngelaAPIClient unavailable:', err.message || err)
      }
    }
  }

  async _sendChat() {
    const input = document.getElementById('chat-input')
    const messages = document.getElementById('chat-messages')
    const text = (input.value || '').trim()
    if (!text || !this.apiClient) return

    this._appendMessage(messages, 'user', text)
    input.value = ''
    try {
      const data = await this.apiClient.sendMessage(text)
      this._appendMessage(messages, 'angela', data?.response || data?.content || '（無回應）')
    } catch (err) {
      this._appendMessage(messages, 'angela', `（連線失敗：${err.message || err}）`)
    }
  }

  _appendMessage(container, role, text) {
    const div = document.createElement('div')
    div.className = `message ${role}`
    div.textContent = text
    container.appendChild(div)
    container.scrollTop = container.scrollHeight
  }

  // ========== System monitor (real ops/status + cluster) ==========

  _wireSystem() {
    const refresh = () => this._refreshSystem()
    refresh()
    setInterval(refresh, 3000)
  }

  async _refreshSystem() {
    try {
      const res = await fetch(`${this.apiBase}/ops/status`, {
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        const data = await res.json()
        const set = (id, v) => {
          const el = document.getElementById(id)
          if (el) el.textContent = v
        }
        set('sys-status', data.status)
        set('sys-service', data.service)
        set('sys-cpu', `${data.metrics?.cpu_percent ?? '—'}%`)
        set('sys-mem', `${data.metrics?.memory_percent ?? '—'}%`)
        set('sys-disk', `${data.metrics?.disk_percent ?? '—'}%`)
      }
    } catch (err) {
      /* backend offline — values stay at — */
    }
    try {
      const res = await fetch(`${this.apiBase}/system/cluster/status`, {
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        const data = await res.json()
        const set = (id, v) => {
          const el = document.getElementById(id)
          if (el) el.textContent = v
        }
        set('sys-nodes', `${data.cluster?.active_nodes ?? 0}/${data.cluster?.total_nodes ?? 0}`)
        set('sys-tier', data.hardware?.performance_tier ?? '—')
        set('sys-ai', data.hardware?.ai_capability_score ?? '—')
      }
    } catch (err) {
      /* ignore */
    }
  }

  // ========== Settings (backend IP + render mode) ==========

  _wireSettings() {
    const ipInput = document.getElementById('settings-backend-ip')
    if (ipInput) ipInput.value = this.baseURL
    const renderSel = document.getElementById('settings-render-mode')
    if (renderSel) {
      renderSel.value = localStorage.getItem('render_mode') || 'live2d'
    }
    document.getElementById('btn-settings-save-ip')?.addEventListener('click', () => {
      const newIP = (ipInput && ipInput.value.trim()) || 'http://localhost:8000'
      localStorage.setItem('backend_ip', newIP)
      this.baseURL = newIP
      this.apiBase = `${newIP}/api/v1`
      if (window.AngelaAPIClient) {
        this.apiClient = new AngelaAPIClient(newIP)
      }
      this._refreshBackendState()
      if (window.MultimodalAPIClient) {
        this.multimodal = new MultimodalAPIClient(newIP)
      }
    })
    document.getElementById('btn-settings-apply-render')?.addEventListener('click', () => {
      localStorage.setItem('render_mode', renderSel.value)
      location.reload()
    })
  }

  // ========== Multimodal (real backend via shared MultimodalAPIClient) ==========

  _wireMultimodal() {
    if (!window.MultimodalAPIClient) return
    try {
      this.multimodal = new MultimodalAPIClient(this.baseURL)
    } catch (err) {
      console.warn('[UnifiedShell] MultimodalAPIClient unavailable:', err.message || err)
      return
    }
    if (this._multimodalWired) return
    this._multimodalWired = true
    this._bindMultimodalTabs()
    this._bindMultimodalVision()
    this._bindMultimodalAudio()
    this._bindMultimodalCompare()
    this._bindMultimodalGenerate()
    this._bindMultimodalItems()
    this._bindMultimodalQuality()
    this._refreshMultimodalHealth()
    this._refreshItemsList()
    this._refreshQuality()
  }

  _bindMultimodalTabs() {
    document.querySelectorAll('#panel-multimodal .mm-tab').forEach((tab) => {
      tab.addEventListener('click', () => {
        document
          .querySelectorAll('#panel-multimodal .mm-tab')
          .forEach((t) => t.classList.remove('active'))
        document
          .querySelectorAll('#panel-multimodal .mm-tab-content')
          .forEach((c) => c.classList.remove('active'))
        tab.classList.add('active')
        const content = document.getElementById(`mm-tab-${tab.dataset.mmTab}`)
        if (content) content.classList.add('active')
      })
    })
  }

  async _refreshMultimodalHealth() {
    const dot = document.getElementById('mm-status-dot')
    const text = document.getElementById('mm-status-text')
    if (!dot || !text || !this.multimodal) return
    const ok = await this.multimodal.checkHealth()
    dot.classList.toggle('offline', !ok)
    text.textContent = ok ? 'Connected' : 'Disconnected'
  }

  _bindMultimodalVision() {
    const zone = document.getElementById('mm-vision-upload')
    const input = document.getElementById('mm-vision-file')
    if (!zone || !input) return
    zone.addEventListener('click', () => input.click())
    zone.addEventListener('dragover', (e) => {
      e.preventDefault()
      zone.classList.add('dragover')
    })
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'))
    zone.addEventListener('drop', (e) => {
      e.preventDefault()
      zone.classList.remove('dragover')
      if (e.dataTransfer.files.length) this._handleVisionFile(e.dataTransfer.files[0])
    })
    input.addEventListener('change', () => {
      if (input.files.length) this._handleVisionFile(input.files[0])
    })
    document
      .getElementById('mm-btn-vision-encode')
      .addEventListener('click', () => this._visionEncode())
    document
      .getElementById('mm-btn-vision-decode')
      .addEventListener('click', () => this._visionDecode())
    this._visionData = null
  }

  _handleVisionFile(file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      this._visionData = e.target.result
      const preview = document.getElementById('mm-vision-preview')
      if (preview)
        preview.innerHTML = `<img src="${this._escapeHtml(e.target.result)}" style="max-width:100%;max-height:140px;border-radius:8px;margin-top:6px">`
    }
    reader.readAsDataURL(file)
  }

  async _visionEncode() {
    if (!this._visionData) return this._showResult('mm-vision-result', { error: '未上傳圖片' })
    const base64 = this._visionData.split(',')[1]
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0))
    const result = await this.multimodal.encode(bytes, 'vision')
    this._showResult('mm-vision-result', result, result.success)
    await this._refreshItemsList()
  }

  async _visionDecode() {
    const items = await this._getItems()
    const vision = Object.entries(items).find(([, v]) => v.modality === 'vision')
    if (!vision) return this._showResult('mm-vision-result', { error: '無 vision 項目' })
    const result = await this.multimodal.decode(vision[0], 'vision')
    this._showResult('mm-vision-result', result, result.success)
  }

  _bindMultimodalAudio() {
    const zone = document.getElementById('mm-audio-upload')
    const input = document.getElementById('mm-audio-file')
    if (!zone || !input) return
    zone.addEventListener('click', () => input.click())
    zone.addEventListener('dragover', (e) => {
      e.preventDefault()
      zone.classList.add('dragover')
    })
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'))
    zone.addEventListener('drop', (e) => {
      e.preventDefault()
      zone.classList.remove('dragover')
      if (e.dataTransfer.files.length) this._handleAudioFile(e.dataTransfer.files[0])
    })
    input.addEventListener('change', () => {
      if (input.files.length) this._handleAudioFile(input.files[0])
    })
    document
      .getElementById('mm-btn-audio-encode')
      .addEventListener('click', () => this._audioEncode())
    document
      .getElementById('mm-btn-audio-decode')
      .addEventListener('click', () => this._audioDecode())
    const rec = document.getElementById('mm-record-btn')
    if (rec) rec.addEventListener('click', () => this._toggleRecord())
    this._audioData = null
  }

  _handleAudioFile(file) {
    const reader = new FileReader()
    reader.onload = async (e) => {
      this._audioData = await this._convertToWav(e.target.result, file.type)
    }
    reader.readAsArrayBuffer(file)
  }

  async _toggleRecord() {
    if (this._mediaRecorder && this._mediaRecorder.state === 'recording') {
      this._mediaRecorder.stop()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      this._mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      this._recChunks = []
      this._mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) this._recChunks.push(e.data)
      }
      this._mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(this._recChunks, { type: 'audio/webm' })
        this._audioData = await this._convertToWav(await blob.arrayBuffer(), 'audio/webm')
        this._showResult('mm-audio-result', {
          status: `已錄音 (${this._audioData.byteLength} bytes)`,
        })
      }
      this._mediaRecorder.start()
      const rec = document.getElementById('mm-record-btn')
      if (rec) rec.classList.add('recording')
    } catch (err) {
      this._showResult('mm-audio-result', { error: `錄音失敗: ${err.message}` })
    }
  }

  async _convertToWav(arrayBuffer, mimeType = 'audio/webm') {
    if (mimeType && mimeType.includes('wav')) return arrayBuffer
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer)
      const numChannels = audioBuffer.numberOfChannels
      const sampleRate = audioBuffer.sampleRate
      const numFrames = audioBuffer.length
      const bytesPerSample = 2
      const blockAlign = numChannels * bytesPerSample
      const buffer = new ArrayBuffer(44 + numFrames * blockAlign)
      const view = new DataView(buffer)
      const writeString = (offset, str) => {
        for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
      }
      writeString(0, 'RIFF')
      view.setUint32(4, 36 + numFrames * blockAlign, true)
      writeString(8, 'WAVE')
      writeString(12, 'fmt ')
      view.setUint32(16, 16, true)
      view.setUint16(20, 1, true)
      view.setUint16(22, numChannels, true)
      view.setUint32(24, sampleRate, true)
      view.setUint32(28, sampleRate * blockAlign, true)
      view.setUint16(32, blockAlign, true)
      view.setUint16(34, 16, true)
      writeString(36, 'data')
      view.setUint32(40, numFrames * blockAlign, true)
      const channels = []
      for (let ch = 0; ch < numChannels; ch++) channels.push(audioBuffer.getChannelData(ch))
      let offset = 44
      for (let i = 0; i < numFrames; i++) {
        for (let ch = 0; ch < numChannels; ch++) {
          const s = Math.max(-1, Math.min(1, channels[ch][i]))
          view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
          offset += bytesPerSample
        }
      }
      if (typeof ctx.close === 'function') ctx.close()
      return buffer
    } catch {
      return arrayBuffer
    }
  }

  async _audioEncode() {
    if (!this._audioData) return this._showResult('mm-audio-result', { error: '未錄音/上傳音檔' })
    const bytes = new Uint8Array(this._audioData)
    const result = await this.multimodal.encode(bytes, 'audio')
    this._showResult('mm-audio-result', result, result.success)
    await this._refreshItemsList()
  }

  async _audioDecode() {
    const items = await this._getItems()
    const audio = Object.entries(items).find(([, v]) => v.modality === 'audio')
    if (!audio) return this._showResult('mm-audio-result', { error: '無 audio 項目' })
    const result = await this.multimodal.decode(audio[0], 'audio')
    this._showResult('mm-audio-result', result, result.success)
  }

  _bindMultimodalCompare() {
    document.getElementById('mm-btn-compare')?.addEventListener('click', async () => {
      const a = document.getElementById('mm-compare-a').value
      const b = document.getElementById('mm-compare-b').value
      if (!a || !b) return this._showResult('mm-compare-result', { error: '請選擇兩端項目' })
      const result = await this.multimodal.compare(a, b)
      this._showResult('mm-compare-result', result, result.success)
    })
  }

  _bindMultimodalGenerate() {
    document.getElementById('mm-btn-generate')?.addEventListener('click', async () => {
      const src = document.getElementById('mm-generate-source').value
      const target = document.getElementById('mm-generate-target').value
      if (!src) return this._showResult('mm-generate-result', { error: '請選擇來源項目' })
      const result = await this.multimodal.generate(src, target)
      this._showResult('mm-generate-result', result, result.success)
    })
  }

  _bindMultimodalItems() {
    document
      .getElementById('mm-btn-refresh')
      ?.addEventListener('click', () => this._refreshItemsList())
    document.getElementById('mm-btn-clear')?.addEventListener('click', async () => {
      const result = await this.multimodal.clearItems()
      this._showResult('mm-vision-result', result, result.success)
      await this._refreshItemsList()
    })
  }

  async _getItems() {
    try {
      const result = await this.multimodal.listItems()
      if (result.success && result.items) return result.items
    } catch (err) {
      /* ignore */
    }
    return {}
  }

  async _refreshItemsList() {
    const list = document.getElementById('mm-items-list')
    if (!list || !this.multimodal) return
    const items = await this._getItems()
    const entries = Object.entries(items)
    const populate = (id) => {
      const sel = document.getElementById(id)
      if (!sel) return
      const current = sel.value
      sel.innerHTML = '<option value="">Select...</option>'
      entries.forEach(([key, item]) => {
        const opt = document.createElement('option')
        opt.value = key
        opt.textContent = `${key} [${item.modality}]`
        sel.appendChild(opt)
      })
      if (current) sel.value = current
    }
    populate('mm-compare-a')
    populate('mm-compare-b')
    populate('mm-generate-source')
    list.textContent = entries.length ? '' : 'No items registered.'
  }

  _bindMultimodalQuality() {
    document
      .getElementById('mm-btn-refresh-quality')
      ?.addEventListener('click', () => this._refreshQuality())
  }

  async _refreshQuality() {
    if (!this.multimodal) return
    try {
      const data = await this.multimodal.qualityDashboard()
      const set = (id, v) => {
        const el = document.getElementById(id)
        if (el) el.textContent = v
      }
      const vision = data.vision || {}
      const audio = data.audio || {}
      set('mm-q-ssim', vision.stats?.avg_ssim?.toFixed(4) ?? vision.avg_ssim?.toFixed(4) ?? '—')
      set('mm-q-psnr', vision.stats?.avg_psnr?.toFixed(1) ?? vision.avg_psnr?.toFixed(1) ?? '—')
      set('mm-q-vision-calls', vision.total_calls ?? 0)
      set('mm-q-snr', audio.stats?.avg_snr?.toFixed(1) ?? audio.avg_snr?.toFixed(1) ?? '—')
      set('mm-q-audio-calls', audio.total_calls ?? 0)
      set('mm-q-health', data.overall_health ?? '—')
      set('mm-q-requests', data.total_requests ?? '—')
    } catch (err) {
      /* ignore */
    }
  }

  _showResult(containerId, data, isSuccess = true) {
    const el = document.getElementById(containerId)
    if (!el) return
    el.style.display = 'block'
    const err = data?.error || (isSuccess === false && '操作失敗')
    if (err || !data) {
      el.innerHTML = `<span style="color:#ff4040">❌ ${this._escapeHtml(String(err))}</span>`
      return
    }
    const keys = Object.keys(data).filter((k) => !['decoded'].includes(k))
    el.innerHTML = keys
      .map((k) => {
        let v = typeof data[k] === 'object' ? JSON.stringify(data[k]) : data[k]
        v = String(v)
        if (v.length > 120) v = v.substring(0, 120) + '...'
        return `<div><span style="color:#4facfe">${this._escapeHtml(k)}:</span> ${this._escapeHtml(v)}</div>`
      })
      .join('')
  }

  _escapeHtml(str) {
    if (typeof str !== 'string') return String(str)
    const div = document.createElement('div')
    div.textContent = str
    return div.innerHTML
  }

  // ========== Game (headless GameEngine REST) ==========

  _wireGame() {
    document.getElementById('btn-game-start')?.addEventListener('click', () => this._gameStart())
    document.getElementById('btn-game-new')?.addEventListener('click', () => this._gameReset())
    document.getElementById('btn-game-act')?.addEventListener('click', () => this._gameAct())
    document.getElementById('game-act-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this._gameAct()
    })
    this._loadGameWorlds()
    this._loadGameCharacters()
  }

  async _loadGameWorlds() {
    const sel = document.getElementById('game-world')
    if (!sel) return
    try {
      const res = await fetch(`${this.apiBase}/game/worlds`, { signal: AbortSignal.timeout(8000) })
      if (!res.ok) return
      const data = await res.json()
      sel.innerHTML = (data.worlds || [])
        .map(
          (w) => `<option value="${this._escapeHtml(w.id)}">${this._escapeHtml(w.name)}</option>`
        )
        .join('')
    } catch (err) {
      console.warn('[UnifiedShell] worlds unavailable:', err.message || err)
    }
  }

  async _loadGameCharacters() {
    const sel = document.getElementById('game-character')
    if (!sel) return
    try {
      const res = await fetch(`${this.apiBase}/game/characters`, {
        signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) return
      const data = await res.json()
      sel.innerHTML = (data.characters || [])
        .map(
          (c) =>
            `<option value="${this._escapeHtml(c.card_id)}">${this._escapeHtml(c.name)}</option>`
        )
        .join('')
    } catch (err) {
      console.warn('[UnifiedShell] characters unavailable:', err.message || err)
    }
  }

  async _gameStart() {
    const pc = document.getElementById('game-character').value
    const world = document.getElementById('game-world').value
    try {
      const res = await fetch(`${this.apiBase}/game/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pc_card_id: pc || 'CC-01',
          scene_card_id: world === 'W02' ? 'S01' : 'S15',
        }),
        signal: AbortSignal.timeout(8000),
      })
      const data = await res.json()
      this.gameSessionId = data.session_id
      this._renderGameState(data.state)
    } catch (err) {
      this._appendGameLine('system', `無法開始遊戲：${err.message || err}`)
    }
  }

  async _gameAct() {
    const input = document.getElementById('game-act-input')
    const text = (input?.value || '').trim()
    if (!this.gameSessionId || !text) return
    input.value = ''
    try {
      const res = await fetch(`${this.apiBase}/game/sessions/${this.gameSessionId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
        signal: AbortSignal.timeout(8000),
      })
      const data = await res.json()
      this._renderGameState(data.state)
    } catch (err) {
      this._appendGameLine('system', `指令失敗：${err.message || err}`)
    }
  }

  async _gameReset() {
    this.gameSessionId = null
    const consoleBox = document.getElementById('game-console')
    if (consoleBox) consoleBox.innerHTML = ''
    const choices = document.getElementById('game-choices')
    if (choices) choices.innerHTML = ''
    const title = document.getElementById('game-scene-title')
    if (title) title.textContent = '未開始'
    await this._gameStart()
  }

  _renderGameState(state) {
    const sceneTitle = document.getElementById('game-scene-title')
    if (sceneTitle) sceneTitle.textContent = `${state.scene?.name || ''} (回合 ${state.turn})`
    const consoleBox = document.getElementById('game-console')
    if (consoleBox) {
      consoleBox.innerHTML = ''
      ;(state.messages || []).forEach((m) => {
        this._appendGameLine(
          m.kind === 'narration'
            ? 'narration'
            : m.kind === 'system'
              ? 'system'
              : m.speaker === '你'
                ? 'player'
                : 'npc',
          `${m.speaker}: ${m.text}`
        )
      })
      const pc = state.pc || {}
      this._appendGameLine(
        'system',
        `—— ${pc.name} ——  HP ${pc.hp}/${pc.max_hp}  靈 ${pc.spirit}/${pc.max_spirit}  技 ${pc.skill}/${pc.max_skill}`
      )
      consoleBox.scrollTop = consoleBox.scrollHeight
    }
    const choices = document.getElementById('game-choices')
    if (choices) {
      choices.innerHTML = ''
      ;(state.choices || []).forEach((label, i) => {
        const btn = document.createElement('button')
        btn.textContent = `${i + 1}. ${label}`
        btn.addEventListener('click', () => {
          const input = document.getElementById('game-act-input')
          if (input) input.value = String(i + 1)
          this._gameAct()
        })
        choices.appendChild(btn)
      })
    }
  }

  _appendGameLine(kind, text) {
    const consoleBox = document.getElementById('game-console')
    if (!consoleBox) return
    const div = document.createElement('div')
    div.className = `game-line ${kind}`
    div.textContent = text
    consoleBox.appendChild(div)
  }
}

// On load (after AngelaApp boots), start the unified shell.
document.addEventListener('DOMContentLoaded', () => {
  window.unifiedShell = new UnifiedShell()
  setTimeout(() => {
    if (window.unifiedShell.init) window.unifiedShell.init()
  }, 500)
})
