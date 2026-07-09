/**
 * =============================================================================
 * ANGELA-MATRIX: L2[UI] [β] [A] [L1]
 * =============================================================================
 *
 * TerminalUI — Frontend terminal overlay with input/output.
 * Provides an additional input pipe alongside the existing chat UI.
 * Flow: original UI → terminal (additional pipe) → backend
 */

class TerminalUI {
  constructor(options = {}) {
    this.onSend = options.onSend || (() => {})
    this.apiClient = options.apiClient || null
    this.isVisible = false
    this._lines = 0
    this._keyHandler = null

    this._createDOM()
    this._bindEvents()

    const parent = options.appendTo || document.body
    parent.appendChild(this.container)
  }

  _createDOM() {
    this.container = document.createElement('div')
    this.container.id = 'terminal-overlay'
    this.container.className = 'terminal-hidden'

    this.container.innerHTML = `
      <div class="terminal-header">
        <span class="terminal-title">Terminal — Angela AI</span>
        <div class="terminal-header-actions">
          <button class="terminal-clear" title="Clear">⌧</button>
          <button class="terminal-close" title="Close (Ctrl+`)">✕</button>
        </div>
      </div>
      <div class="terminal-output"></div>
      <div class="terminal-input-line">
        <span class="terminal-prompt">$</span>
        <input type="text" class="terminal-input" placeholder="Type a message or command..." spellcheck="false" autocomplete="off" />
      </div>
    `

    this.output = this.container.querySelector('.terminal-output')
    this.input = this.container.querySelector('.terminal-input')
  }

  _bindEvents() {
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const text = this.input.value.trim()
        if (!text) return
        this.write(`> ${text}`, 'input')
        this.onSend(text)
        this.input.value = ''
      }
    })

    this.container.querySelector('.terminal-close').addEventListener('click', () => this.hide())
    this.container.querySelector('.terminal-clear').addEventListener('click', () => this.clear())
  }

  /** Write a line to the terminal output */
  write(text, type = 'system') {
    const line = document.createElement('div')
    line.className = `terminal-line terminal-${type}`
    line.textContent = text
    this.output.appendChild(line)
    this.output.scrollTop = this.output.scrollHeight
    this._lines++
    if (this._lines > 500) {
      const excess = this._lines - 500
      for (let i = 0; i < excess; i++) {
        if (this.output.firstChild) this.output.removeChild(this.output.firstChild)
      }
      this._lines = 500
    }
  }

  /** Write a backend response line */
  writeResponse(text) {
    this.write(text, 'response')
  }

  /** Write a system message */
  writeSystem(text) {
    this.write(text, 'system')
  }

  /** Clear all output */
  clear() {
    this.output.innerHTML = ''
    this._lines = 0
  }

  toggle() {
    this.isVisible ? this.hide() : this.show()
  }

  show() {
    this.isVisible = true
    this.container.classList.remove('terminal-hidden')
    this.container.classList.add('terminal-visible')
    setTimeout(() => this.input.focus(), 50)
  }

  hide() {
    this.isVisible = false
    this.container.classList.remove('terminal-visible')
    this.container.classList.add('terminal-hidden')
  }

  /** Register global Ctrl+` toggle. Call once after construction */
  registerGlobalShortcut() {
    if (this._keyHandler) return
    this._keyHandler = (e) => {
      if (e.ctrlKey && e.key === '`') {
        e.preventDefault()
        this.toggle()
      }
    }
    document.addEventListener('keydown', this._keyHandler)
  }

  destroy() {
    if (this._keyHandler) {
      document.removeEventListener('keydown', this._keyHandler)
    }
    if (this.container.parentNode) {
      this.container.parentNode.removeChild(this.container)
    }
  }
}
