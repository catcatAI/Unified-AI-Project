# Cross-Platform Testing Guide

This guide provides comprehensive testing procedures for the Angela AI Desktop Application across Windows, macOS, and Linux.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Native Module Setup](#native-module-setup)
3. [Platform-Specific Testing](#platform-specific-testing)
4. [Live2D Integration Testing](#live2d-integration-testing)
5. [System Audio Testing](#system-audio-testing)
6. [Integration Testing](#integration-testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Common Requirements

- **Node.js**: >= 16.0.0
- **npm**: >= 8.0.0
- **Python**: 3.8+ (for node-gyp)
- **C++ Compiler**: Platform-specific (see below)

### Windows Requirements

- **Visual Studio Build Tools** (2019 or later)
- **Windows SDK**: 10.0.19041.0 or later
- **CMake**: 3.15+ (optional but recommended)

**Install Visual Studio Build Tools:**
```powershell
winget install Microsoft.VisualStudio.2022.BuildTools
```

### macOS Requirements

- **Xcode Command Line Tools**:
```bash
xcode-select --install
```

- **Xcode**: Latest version from App Store (for full development)

### Linux Requirements

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    pkg-config \
    libpulse-dev \
    libasound2-dev
```

**Fedora/RHEL:**
```bash
sudo dnf install -y \
    gcc-c++ \
    make \
    pulseaudio-libs-devel \
    alsa-lib-devel
```

---

## Native Module Setup

### Building Native Modules

Navigate to each native module directory and build:

```bash
# Windows WASAPI
cd apps/desktop-app/native_modules/node-wasapi-capture
npm install

# macOS CoreAudio
cd ../node-coreaudio-capture
npm install

# Linux PulseAudio
cd ../node-pulseaudio-capture
npm install
```

### Test Native Modules Individually

**Windows:**
```bash
cd apps/desktop-app/native_modules/node-wasapi-capture
npm test
```

**macOS:**
```bash
cd apps/desktop-app/native_modules/node-coreaudio-capture
npm test
```

**Linux:**
```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
npm test
```

---

## Platform-Specific Testing

### Windows Testing

#### 1. Installation Testing

```powershell
# Navigate to the app directory
cd apps/desktop-app

# Install dependencies
npm install

# Build native modules
cd native_modules/node-wasapi-capture
npm install

# Start development server
cd ../..
npm start
```

#### 2. System Tray Testing

- [ ] Tray icon appears in system tray
- [ ] Right-click shows context menu
- [ ] All 12 menu items are present:
  - Show/Hide Angela
  - Settings
  - Reload Model
  - Auto-startup (with checkbox)
  - Toggle Always on Top
  - Toggle Frame
  - About
  - Check for Updates
  - Restart
  - Quit
- [ ] Double-click toggles window visibility
- [ ] "Always on Top" toggle works
- [ ] "Toggle Frame" works

#### 3. Auto-Startup Testing

```powershell
# Check registry for auto-startup entry
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "AngelaAI"
```

- [ ] Auto-startup checkbox reflects current state
- [ ] Enabling auto-startup creates registry entry
- [ ] Disabling auto-startup removes registry entry
- [ ] Application starts with system when enabled

#### 4. Desktop Integration Testing

- [ ] Angela appears on desktop
- [ ] Desktop shortcuts remain clickable
- [ ] Click-through works when interacting with desktop icons
- [ ] Right-click on desktop icons shows context menu
- [ ] Angela responds to mouse/touch interactions

#### 5. WASAPI Audio Testing

- [ ] Native module loads successfully
- [ ] System audio device list is populated
- [ ] Default device is detected
- [ ] System audio capture starts without errors
- [ ] Audio samples are received
- [ ] Audio levels are detected correctly

---

### macOS Testing

#### 1. Installation Testing

```bash
# Navigate to the app directory
cd apps/desktop-app

# Install dependencies
npm install

# Build native modules
cd native_modules/node-coreaudio-capture
npm install

# Start development server
cd ../..
npm start
```

#### 2. System Tray Testing

- [ ] Menu bar icon appears
- [ ] Click shows dropdown menu
- [ ] All menu items are present and functional
- [ ] Double-click works correctly

#### 3. Auto-Startup Testing

```bash
# Check login items
osascript -e 'tell application "System Events" to get the name of every login item'
```

- [ ] Auto-startup checkbox reflects current state
- [ ] Enabling creates login item
- [ ] Disabling removes login item
- [ ] Application starts on login when enabled

#### 4. Desktop Integration Testing

- [ ] Angela appears on desktop
- [ ] Desktop items remain interactive
- [ ] Click-through works correctly
- [ ] Right-click on desktop icons shows menu
- [ ] Angela responds to interactions

#### 5. CoreAudio Testing

- [ ] Native module loads successfully
- [ ] Audio device list is populated
- [ ] Default device is detected
- [ ] System audio capture starts without errors
- [ ] Audio samples are received
- [ ] Audio levels are detected correctly

---

### Linux Testing

#### 1. Installation Testing

```bash
# Navigate to the app directory
cd apps/desktop-app

# Install dependencies
npm install

# Build native modules
cd native_modules/node-pulseaudio-capture
npm install

# Start development server
cd ../..
npm start
```

#### 2. System Tray Testing

- [ ] System tray icon appears (if supported by desktop environment)
- [ ] Context menu shows all options
- [ ] Menu items work correctly

#### 3. Auto-Startup Testing

```bash
# Check autostart directory
ls -la ~/.config/autostart/
```

- [ ] Auto-startup creates .desktop file in ~/.config/autostart/
- [ ] .desktop file has correct permissions
- [ ] Application starts on login
- [ ] Disabling removes .desktop file

#### 4. Desktop Integration Testing

- [ ] Angela appears on desktop
- [ ] Desktop environment integration works
- [ ] Click-through works correctly
- [ ] Desktop shortcuts remain functional

#### 5. PulseAudio Testing

- [ ] Native module loads successfully
- [ ] PulseAudio daemon is detected
- [ ] Audio device list shows available sinks
- [ ] Default sink is detected
- [ ] System audio capture starts without errors
- [ ] Audio samples are received
- [ ] Audio levels are detected correctly

---

## Live2D Integration Testing

### Running Live2D Test Suite

Open the browser console and run:

```javascript
// Create test suite
const testSuite = new Live2DTestSuite();

// Initialize with canvas
const canvas = document.getElementById('live2d-canvas');
await testSuite.initialize(canvas);

// Run all tests
await testSuite.runAllTests();
```

### Expected Test Results

All tests should pass with performance >= 80%:

```
✓ SDK Loading: Cubism SDK loaded successfully
✓ Cubism Loading: Cubism core loaded successfully
✓ Renderer Ready: Renderer initialized successfully
✓ Model Loading: Model loaded successfully
✓ Model Instance: Model instance created
✓ Canvas Size: Canvas: 800x600
✓ Motion: idle: Motion played successfully
✓ Motion: greeting: Motion played successfully
✓ Motion: thinking: Motion played successfully
✓ Motion: dancing: Motion played successfully
✓ Motion: waving: Motion played successfully
✓ Motion: clapping: Motion played successfully
✓ Motion: nod: Motion played successfully
✓ Motion: shake: Motion played successfully
✓ Expression: neutral: Expression applied successfully
✓ Expression: happy: Expression applied successfully
✓ Expression: sad: Expression applied successfully
✓ Expression: angry: Expression applied successfully
✓ Expression: surprised: Expression applied successfully
✓ Expression: shy: Expression applied successfully
✓ Expression: love: Expression applied successfully
✓ Physics Enable: Physics enabled
✓ Physics Disable: Physics disabled
✓ Lip Sync Enable: Lip sync enabled
✓ Lip Sync Update: Lip sync values updated
✓ Lip Sync Disable: Lip sync disabled
✓ Auto Blink Enable: Auto blink enabled
✓ Auto Blink Disable: Auto blink disabled
✓ Breathing Enable: Breathing enabled
✓ Breathing Disable: Breathing disabled
✓ Eye Tracking: Eye tracking updated for multiple positions
✓ Performance: Target: 60 FPS, Actual: 59.8 FPS (99.7%)
✓ Memory Usage: Memory: 45.23 MB
```

### Manual Live2D Testing

- [ ] Model renders correctly
- [ ] Model scales to window size
- [ ] All 7 expressions work:
  - [ ] Neutral
  - [ ] Happy
  - [ ] Sad
  - [ ] Angry
  - [ ] Surprised
  - [ ] Shy
  - [ ] Love
- [ ] All 10 motions play smoothly:
  - [ ] Idle
  - [ ] Greeting
  - [ ] Thinking
  - [ ] Dancing
  - [ ] Waving
  - [ ] Clapping
  - [ ] Nod
  - [ ] Shake
- [ ] Physics simulation is visible
- [ ] Lip sync responds to audio
- [ ] Auto-blinking occurs naturally
- [ ] Breathing animation is visible
- [ ] Eyes follow mouse cursor
- [ ] Mouse interactions work:
  - [ ] Click
  - [ ] Drag
  - [ ] Track
  - [ ] Hover

---

## System Audio Testing

### Windows WASAPI Testing

1. **Device Enumeration:**
```javascript
const devices = WASAPICapture.getDevices();
console.log(devices);
```

- [ ] All output devices are listed
- [ ] Device names are correct
- [ ] Device IDs are valid

2. **Default Device:**
```javascript
const defaultDevice = WASAPICapture.getDefaultDevice();
console.log(defaultDevice);
```

- [ ] Default device is detected
- [ ] Default device matches system settings

3. **Audio Capture:**
```javascript
const capture = new WASAPICapture();
await capture.start(null, (samples) => {
    console.log('Received', samples.length, 'samples');
});
```

- [ ] Capture starts without errors
- [ ] Samples are received continuously
- [ ] Audio levels vary correctly
- [ ] No audio dropouts
- [ ] CPU usage remains reasonable (< 10%)

### macOS CoreAudio Testing

1. **Device Enumeration:**
```javascript
const devices = CoreAudioCapture.getDevices();
console.log(devices);
```

- [ ] All output devices are listed
- [ ] Device names are correct
- [ ] Device IDs are valid

2. **Default Device:**
```javascript
const defaultDevice = CoreAudioCapture.getDefaultDevice();
console.log(defaultDevice);
```

- [ ] Default device is detected
- [ ] Default device matches system settings

3. **Audio Capture:**
```javascript
const capture = new CoreAudioCapture();
await capture.start(null, (samples) => {
    console.log('Received', samples.length, 'samples');
});
```

- [ ] Capture starts without errors
- [ ] Samples are received continuously
- [ ] Audio levels vary correctly
- [ ] No audio dropouts
- [ ] CPU usage remains reasonable (< 10%)

### Linux PulseAudio Testing

1. **Device Enumeration:**
```javascript
const devices = PulseAudioCapture.getDevices();
console.log(devices);
```

- [ ] All sink monitors are listed
- [ ] Device names are correct
- [ ] Device descriptions are present

2. **Default Device:**
```javascript
const defaultDevice = PulseAudioCapture.getDefaultDevice();
console.log(defaultDevice);
```

- [ ] Default sink is detected
- [ ] Default sink matches system settings

3. **Audio Capture:**
```javascript
const capture = new PulseAudioCapture();
await capture.start(null, (samples) => {
    console.log('Received', samples.length, 'samples');
});
```

- [ ] Capture starts without errors
- [ ] Samples are received continuously
- [ ] Audio levels vary correctly
- [ ] No audio dropouts
- [ ] CPU usage remains reasonable (< 10%)

---

## Integration Testing

### Full Application Flow

1. **Startup:**
   - [ ] Application launches without errors
   - [ ] Loading screens display correctly
   - [ ] Model loads successfully
   - [ ] Settings are restored
   - [ ] WebSocket connection establishes
   - [ ] System tray icon appears

2. **User Interaction:**
   - [ ] Clicking Angela triggers response
   - [ ] Dragging Angela works
   - [ ] Settings page opens correctly
   - [ ] Theme switching works
   - [ ] Language switching works
   - [ ] Model switching works

3. **Audio:**
   - [ ] Microphone input works
   - [ ] System audio capture works
   - [ ] TTS playback works
   - [ ] Lip sync works
   - [ ] Audio visualization works

4. **Backend Communication:**
   - [ ] State matrix syncs
   - [ ] Maturity level updates
   - [ ] Precision mode changes
   - [ ] Hardware detection syncs
   - [ ] Reconnection works on disconnect

5. **Shutdown:**
   - [ ] Clean shutdown process
   - [ ] All resources released
   - [ ] Settings saved
   - [ ] Window closes properly

---

## Troubleshooting

### Common Issues

#### Native Module Build Failures

**Windows:**
```powershell
# Clear node-gyp cache
rd /s /q %APPDATA%\..\Local\node-gyp\Cache

# Reinstall build tools
npm install --global windows-build-tools

# Rebuild module
npm install
```

**macOS:**
```bash
# Clear node-gyp cache
rm -rf ~/.node-gyp

# Reinstall Xcode Command Line Tools
sudo xcode-select --install

# Rebuild module
npm install
```

**Linux:**
```bash
# Clear node-gyp cache
rm -rf ~/.node-gyp

# Install required dependencies
sudo apt-get install build-essential

# Rebuild module
npm install
```

#### Live2D Model Not Loading

- Check model path in settings
- Verify all model files exist:
  - `.moc3` file
  - `.model3.json` file
  - `.physics3.json` file
  - `.cdi3.json` file
  - Texture files (`.png`)
  - Motion files (`.motion3.json`)
- Check browser console for CORS errors

#### System Audio Not Capturing

**Windows:**
- Ensure WASAPI is enabled in Windows settings
- Check Windows privacy settings for microphone/audio access
- Run application as administrator if needed

**macOS:**
- Grant microphone/audio permissions in System Preferences
- Check security settings for CoreAudio access
- Ensure PulseAudio is running (Linux)

**Linux:**
- Ensure PulseAudio daemon is running: `pulseaudio --check -v`
- Check user permissions for audio devices
- Verify monitor sources are available: `pactl list sources`

#### Performance Issues

- Check hardware detection results
- Adjust performance mode in settings
- Reduce animation quality if needed
- Close other resource-intensive applications

---

## Test Checklist Summary

### Installation
- [ ] Application installs correctly
- [ ] Native modules build successfully
- [ ] All dependencies resolve

### Functionality
- [ ] Live2D model renders
- [ ] All animations play
- [ ] System audio captures
- [ ] Microphone works
- [ ] TTS plays
- [ ] Settings save/restore

### Integration
- [ ] Backend sync works
- [ ] WebSocket connects
- [ ] State matrix updates
- [ ] Performance scales correctly

### User Experience
- [ ] System tray works
- [ ] Auto-startup works
- [ ] Desktop integration works
- [ ] Click-through works

### Cross-Platform
- [ ] Windows: All features work
- [ ] macOS: All features work
- [ ] Linux: All features work

---

## Reporting Issues

When reporting issues, include:

1. Platform and version
2. Node.js version
3. Application version
4. Steps to reproduce
5. Expected vs actual behavior
6. Console logs/errors
7. Screenshot/video if applicable

---

## Performance Benchmarks

### Expected Performance

| Component | Target | Minimum |
|-----------|--------|---------|
| Live2D FPS | 60 | 30 |
| Audio Latency | < 50ms | < 100ms |
| Memory Usage | < 100MB | < 200MB |
| CPU Usage | < 5% | < 15% |

---

## Conclusion

This testing guide ensures comprehensive coverage of all Angela AI Desktop Application features across all supported platforms. Regular testing during development and before releases is essential for maintaining high quality and user satisfaction.
