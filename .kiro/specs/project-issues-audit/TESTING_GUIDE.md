# Angela AI - Complete Testing Guide

**Date**: 2026-02-07  
**Version**: 6.2.0  
**Status**: Ready for Testing

---

## Prerequisites

### System Requirements

**Backend**:
- Python 3.8+
- pip package manager
- Port 8000 available

**Desktop App**:
- Node.js 14+
- npm package manager
- Electron compatible OS (Windows/macOS/Linux)

**Mobile App**:
- Node.js 14+
- React Native CLI
- Android Studio (for Android) or Xcode (for iOS)

---

## Phase 1: Backend Testing ✅ PASSED

### 1.1 Start Backend

```bash
cd apps/backend
python main.py
```

### 1.2 Expected Output

```
✅ All core components initialized successfully
✅ Unified Control Center ACTIVE with 4 workers
✅ Brain Bridge Service started
✅ Brain Metrics Synced: L_=0.4157, Λ_=0.0000
✅ Angela 已啟動!
按 Ctrl+C 退出
```

### 1.3 Verification

- [ ] Backend starts without errors
- [ ] Port 8000 is listening
- [ ] All modules initialized
- [ ] No import errors
- [ ] No syntax errors

**Status**: ✅ PASSED (2026-02-07)

---

## Phase 2: Backend API Testing

### 2.1 Health Check

```bash
curl http://127.0.0.1:8000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T..."
}
```

### 2.2 Key C Sync Endpoint

```bash
curl http://127.0.0.1:8000/api/v1/security/sync-key-c
```

**Expected Response**:
```json
{
  "key_c": "...",
  "timestamp": "2026-02-07T..."
}
```

### 2.3 WebSocket Connection Test

Using `wscat` (install: `npm install -g wscat`):

```bash
wscat -c ws://127.0.0.1:8000/ws
```

**Expected**:
- Connection established
- Can send/receive messages

**Test Message**:
```json
{"type": "ping", "timestamp": 1234567890}
```

**Expected Response**:
```json
{"type": "pong", "timestamp": "2026-02-07T..."}
```

### 2.4 Verification Checklist

- [ ] Health endpoint responds
- [ ] Key C sync endpoint responds
- [ ] WebSocket connection works
- [ ] Ping/pong works
- [ ] No errors in backend logs

---

## Phase 3: Desktop App Testing ⏳ PENDING

### 3.1 Install Dependencies

```bash
cd apps/desktop-app/electron_app
npm install
```

### 3.2 Start Desktop App

```bash
npm start
```

**Alternative (with DevTools)**:
```bash
npm run dev
```

### 3.3 Expected Behavior

**Window**:
- Electron window opens
- Transparent background (if configured)
- No frame (frameless window)
- System tray icon appears

**Console Output** (check DevTools):
```
[WebSocket] Connecting to ws://127.0.0.1:8000/ws...
[WebSocket] Connected successfully
🔐 Loaded Key C from local storage (or)
🔄 Syncing Key C from backend...
✅ Key C synced successfully
```

**Live2D**:
- Model loads (or shows error if model files missing)
- Animation plays
- Model responds to mouse interaction

### 3.4 Verification Checklist

- [ ] App starts without errors
- [ ] Window opens
- [ ] System tray icon appears
- [ ] WebSocket connects to backend
- [ ] Key C syncs successfully
- [ ] Live2D model loads (or graceful error)
- [ ] No JavaScript errors in console

### 3.5 Common Issues

**Issue**: Window doesn't open
- Check Node.js version: `node --version`
- Check Electron installation: `npm list electron`
- Check console for errors

**Issue**: WebSocket won't connect
- Verify backend is running
- Check URL in console
- Check firewall settings

**Issue**: Live2D model won't load
- Check model files exist in `resources/models/`
- Check console for path errors
- Verify Cubism SDK loaded

**Issue**: Key C sync fails
- Verify backend is running
- Check `/api/v1/security/sync-key-c` endpoint
- Check network connectivity

---

## Phase 4: Desktop App Feature Testing

### 4.1 WebSocket Communication

**Test**: Send message to backend

1. Open DevTools console
2. Execute:
```javascript
window.electronAPI.websocketSend({
  type: 'ping',
  timestamp: Date.now()
});
```

3. Check for response in console

**Expected**: Pong response received

### 4.2 Module Control

**Test**: Toggle module state

1. Right-click system tray icon
2. Navigate to "Angela Matrix"
3. Toggle "Vision System" checkbox

**Expected**:
- Checkbox state changes
- Backend receives module_control message
- Backend broadcasts status change
- All connected clients update

### 4.3 Calculator Tool Test

**Test**: Execute calculator tool through WebSocket

1. Open DevTools console
2. Execute:
```javascript
window.electronAPI.websocketSend({
  type: 'tool_execute',
  tool: 'calculator',
  expression: '2 + 2'
});
```

3. Check for response

**Expected**: Result = 4

### 4.4 Performance Mode

**Test**: Change performance mode

1. Right-click system tray icon
2. Navigate to "Hardware & Performance" → "Performance Mode"
3. Select "Ultra"

**Expected**:
- Mode changes
- Backend receives update
- Performance adjusts

### 4.5 Verification Checklist

- [ ] WebSocket send/receive works
- [ ] Module control works
- [ ] Calculator tool works
- [ ] Performance mode changes
- [ ] System tray menu works
- [ ] Settings window opens

---

## Phase 5: Mobile App Testing ⏳ PENDING

### 5.1 Install Dependencies

```bash
cd apps/mobile-app
npm install
```

### 5.2 Android Build

```bash
npm run android
```

**Requirements**:
- Android Studio installed
- Android SDK configured
- Android device or emulator running

### 5.3 iOS Build

```bash
npm run ios
```

**Requirements**:
- Xcode installed (macOS only)
- iOS Simulator or device
- Apple Developer account (for device)

### 5.4 Expected Behavior

**App Launch**:
- App opens without crashes
- Version displays: "v6.2"
- QR code scanner available

**QR Code Pairing**:
- Scan QR code from desktop app
- Receive Key C
- Establish encrypted connection

**Communication**:
- Send encrypted messages
- Receive responses
- Real-time sync with backend

### 5.5 Verification Checklist

- [ ] App builds successfully
- [ ] App launches without crashes
- [ ] QR code scanner works
- [ ] Pairing process works
- [ ] Encrypted communication works
- [ ] Backend connection stable

---

## Phase 6: Integration Testing

### 6.1 Multi-Client Test

**Setup**:
1. Start backend
2. Start desktop app
3. Start mobile app (if available)

**Test**: Module control sync

1. Toggle module in desktop app
2. Verify mobile app receives update
3. Toggle module in mobile app
4. Verify desktop app receives update

**Expected**: All clients stay in sync

### 6.2 Tool Execution Test

**Test**: Execute tools from different clients

1. Desktop app: Execute calculator tool
2. Mobile app: Execute calculator tool
3. Verify both receive correct results

**Expected**: Tools work from all clients

### 6.3 Reconnection Test

**Test**: Backend restart

1. Stop backend (Ctrl+C)
2. Wait 5 seconds
3. Restart backend
4. Verify clients reconnect automatically

**Expected**: Auto-reconnect works

### 6.4 Verification Checklist

- [ ] Multiple clients can connect
- [ ] State syncs across clients
- [ ] Tools work from all clients
- [ ] Auto-reconnect works
- [ ] No data loss on reconnect

---

## Phase 7: Performance Testing

### 7.1 Load Test

**Test**: Multiple WebSocket connections

1. Start backend
2. Connect 10 desktop app instances
3. Send messages from all clients
4. Monitor backend performance

**Expected**:
- All connections stable
- No memory leaks
- Reasonable CPU usage

### 7.2 Long-Running Test

**Test**: 24-hour stability

1. Start all components
2. Let run for 24 hours
3. Monitor for crashes or errors

**Expected**:
- No crashes
- No memory leaks
- Stable performance

### 7.3 Verification Checklist

- [ ] Handles multiple connections
- [ ] No memory leaks
- [ ] Stable over time
- [ ] Reasonable resource usage

---

## Troubleshooting

### Backend Issues

**Error**: `ModuleNotFoundError`
- **Fix**: Install missing dependencies: `pip install -r requirements.txt`

**Error**: `Port 8000 already in use`
- **Fix**: Kill process using port: `lsof -ti:8000 | xargs kill -9` (macOS/Linux)
- **Fix**: Change port in `main.py`

**Error**: `ImportError: cannot import name 'X'`
- **Fix**: Check import paths in code
- **Fix**: Verify module exists

### Desktop App Issues

**Error**: `Cannot find module 'electron'`
- **Fix**: `npm install electron`

**Error**: `WebSocket connection failed`
- **Fix**: Verify backend is running
- **Fix**: Check URL: `ws://127.0.0.1:8000/ws`
- **Fix**: Check firewall

**Error**: `Live2D model not found`
- **Fix**: Verify model files in `resources/models/`
- **Fix**: Check model path in code

**Error**: `Key C sync failed`
- **Fix**: Verify backend endpoint: `curl http://127.0.0.1:8000/api/v1/security/sync-key-c`
- **Fix**: Check network connectivity

### Mobile App Issues

**Error**: `Build failed`
- **Fix**: Check Android Studio/Xcode installation
- **Fix**: Check SDK configuration
- **Fix**: Run `npm install` again

**Error**: `App crashes on launch`
- **Fix**: Check logs: `adb logcat` (Android) or Xcode console (iOS)
- **Fix**: Verify all dependencies installed

---

## Success Criteria

### Minimum Viable Product (MVP)

- [x] Backend starts without errors ✅
- [ ] Desktop app starts without errors
- [ ] WebSocket connection established
- [ ] At least one tool works (calculator)
- [ ] Key C sync works

### Production Ready

- [ ] All apps start successfully
- [ ] All WebSocket connections work
- [ ] All tools execute correctly
- [ ] Mobile app builds successfully
- [ ] Integration tests pass
- [ ] No critical bugs
- [ ] Performance acceptable

---

## Test Results Log

### Backend Test - 2026-02-07

**Tester**: Kiro AI  
**Result**: ✅ PASSED

**Details**:
- Backend started successfully
- All modules initialized
- No errors in console
- Port 8000 listening

**Evidence**: Screenshot showing successful startup

---

### Desktop App Test - Pending

**Tester**: TBD  
**Result**: ⏳ PENDING

**Next Steps**:
1. Run `npm start` in desktop app directory
2. Verify window opens
3. Check WebSocket connection
4. Test tool execution

---

## Conclusion

**Current Status**: Backend verified working, desktop app ready for testing.

**Next Action**: Execute Phase 3 (Desktop App Testing)

**Estimated Time**: 30-60 minutes for complete testing

---

*This testing guide provides step-by-step instructions for verifying all components of the Angela AI system.*
