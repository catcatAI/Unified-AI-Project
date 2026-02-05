import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TextInput, 
  ScrollView, 
  TouchableOpacity, 
  SafeAreaView, 
  StatusBar,
  Dimensions,
  Animated,
  Alert
} from 'react-native';
import QRCodeScanner from 'react-native-qrcode-scanner';
import { RNCamera } from 'react-native-camera';
import security from './src/security/encryption';

const { width } = Dimensions.get('window');

const App = () => {
  const [status, setStatus] = useState('OFFLINE');
  const [keyB, setKeyB] = useState('');
  const [showScanner, setShowScanner] = useState(false);
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState([
    { type: 'angela', text: 'System initialized. Waiting for secure link...' }
  ]);
  const [isSecure, setIsSecure] = useState(false);
  const [systemStats, setSystemStats] = useState({ cpu: '0%', mem: '0%', nodes: 0 });
  const [modules, setModules] = useState({
    vision: true,
    audio: true,
    tactile: true,
    action: true
  });
  const [matrixState, setMatrixState] = useState({
    emotion: 0.5,
    cognition: 0.5,
    memory: 0.5,
    stability: 0.5
  });

  const scrollRef = useRef();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const matrixAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();

    // 矩陣動畫循環
    Animated.loop(
      Animated.sequence([
        Animated.timing(matrixAnim, {
          toValue: 1,
          duration: 3000,
          useNativeDriver: true,
        }),
        Animated.timing(matrixAnim, {
          toValue: 0,
          duration: 3000,
          useNativeDriver: true,
        })
      ])
    ).start();
  }, []);

  // 定期獲取系統狀態
  useEffect(() => {
    let interval;
    if (isSecure) {
      interval = setInterval(fetchSystemStatus, 3000);
    }
    return () => clearInterval(interval);
  }, [isSecure]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollToEnd({ animated: true });
    }
  }, [chatLog]);

  const fetchSystemStatus = async () => {
    try {
      const backendHost = 'localhost:8000'; 
      const data = await security.securePost(`http://${backendHost}/api/v1/system/status`, {
        action: 'get_status',
        timestamp: Date.now()
      });
      
      // 這裡模擬從後端獲取矩陣狀態
      setMatrixState({
        emotion: 0.4 + Math.random() * 0.2,
        cognition: 0.6 + Math.random() * 0.3,
        memory: 0.8 + Math.random() * 0.1,
        stability: 0.9 + Math.random() * 0.05
      });

      setSystemStats({
        cpu: (Math.random() * 15 + 5).toFixed(1) + '%',
        mem: (Math.random() * 10 + 35).toFixed(1) + '%',
        nodes: 1 + Math.floor(Math.random() * 3)
      });
      setStatus('SECURE LINK ACTIVE');
    } catch (error) {
      setStatus('LINK INTERRUPTED');
    }
  };

  const MatrixIndicator = ({ label, value, color }) => (
    <View style={styles.matrixItem}>
      <Text style={[styles.matrixLabel, { color }]}>{label}</Text>
      <View style={styles.matrixBarBg}>
        <View style={[styles.matrixBarFill, { width: `${value * 100}%`, backgroundColor: color }]} />
      </View>
    </View>
  );

  const toggleModule = async (modName) => {
    const newState = !modules[modName];
    setModules(prev => ({
      ...prev,
      [modName]: newState
    }));

    if (isSecure) {
      try {
        await security.securePost('http://localhost:8000/api/v1/system/module-control', {
          module: modName,
          enabled: newState,
          timestamp: Date.now()
        });
      } catch (error) {
        console.log('Control Sync Error');
      }
    }
  };

  const handleInit = (manualKey) => {
    const targetKey = manualKey || keyB;
    if (targetKey.length < 16) {
      setStatus('KEY INVALID');
      Alert.alert('Error', 'Security Key B must be at least 16 characters.');
      return;
    }
    security.init(targetKey);
    setIsSecure(true);
    setStatus('SECURE LINK ESTABLISHED');
    setChatLog(prev => [...prev, { type: 'angela', text: 'Secure handshake complete. Welcome back, Commander.' }]);
  };

  const onQRCodeRead = (e) => {
    setShowScanner(false);
    setKeyB(e.data);
    handleInit(e.data);
  };

  const sendSecureRequest = async () => {
    if (!message.trim() || !isSecure) return;
    
    const userMsg = message;
    setMessage('');
    setChatLog(prev => [...prev, { type: 'user', text: userMsg }]);

    try {
      const result = await security.securePost('http://localhost:8000/api/v1/mobile/test', {
        message: userMsg,
        timestamp: Date.now(),
        client: 'Angela-Mobile-V6'
      });
      
      setChatLog(prev => [...prev, { type: 'angela', text: result.message }]);
    } catch (error) {
      setChatLog(prev => [...prev, { type: 'angela', text: 'Error: Connection lost. Re-encrypting...' }]);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      <Animated.View style={[styles.innerContainer, { opacity: fadeAnim }]}>
        
        {/* Header - Status Bar */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>ANGELA CORE v6.1</Text>
            <View style={styles.statusRow}>
              <View style={[styles.statusDot, { backgroundColor: isSecure ? '#00ffcc' : '#ff3366' }]} />
              <Text style={[styles.headerStatus, { color: isSecure ? '#00ffcc' : '#ff3366' }]}>
                {status}
              </Text>
            </View>
          </View>
          <View style={styles.statsContainer}>
            <Text style={styles.statText}>CPU: {systemStats.cpu}</Text>
            <Text style={styles.statText}>MEM: {systemStats.mem}</Text>
            <Text style={styles.statText}>NODES: {systemStats.nodes}</Text>
          </View>
        </View>

        {!isSecure ? (
          /* Pairing View */
          showScanner ? (
            <View style={styles.scannerContainer}>
              <QRCodeScanner
                onRead={onQRCodeRead}
                flashMode={RNCamera.Constants.FlashMode.auto}
                topContent={
                  <Text style={styles.scannerText}>Align QR Code with the frame</Text>
                }
                bottomContent={
                  <TouchableOpacity style={styles.cancelButton} onPress={() => setShowScanner(false)}>
                    <Text style={styles.cancelButtonText}>CANCEL</Text>
                  </TouchableOpacity>
                }
              />
            </View>
          ) : (
            <View style={styles.pairingContainer}>
              <Text style={styles.pairingLabel}>SECURE PAIRING REQUIRED</Text>
              
              <TouchableOpacity style={styles.qrButton} onPress={() => setShowScanner(true)}>
                <Text style={styles.qrButtonText}>SCAN QR CODE</Text>
              </TouchableOpacity>

              <View style={styles.divider}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>OR</Text>
                <View style={styles.dividerLine} />
              </View>

              <TextInput
                style={styles.keyInput}
                placeholder="ENTER KEY B MANUALLY"
                placeholderTextColor="#666"
                value={keyB}
                onChangeText={setKeyB}
                secureTextEntry
                autoCapitalize="none"
              />
              <TouchableOpacity style={styles.initButton} onPress={() => handleInit()}>
                <Text style={styles.initButtonText}>ESTABLISH LINK</Text>
              </TouchableOpacity>
              <Text style={styles.pairingHint}>
                * Get QR Code from the Angela Desktop Security Monitor tray icon.
              </Text>
            </View>
          )
        ) : (
          /* Main AGI Interface */
          <View style={styles.mainInterface}>
            {/* 4D Matrix State Visualization */}
            <View style={styles.matrixContainer}>
              <View style={styles.matrixGrid}>
                <MatrixIndicator label="EMO" value={matrixState.emotion} color="#ff3366" />
                <MatrixIndicator label="COG" value={matrixState.cognition} color="#33ccff" />
                <MatrixIndicator label="MEM" value={matrixState.memory} color="#ffcc33" />
                <MatrixIndicator label="STB" value={matrixState.stability} color="#00ffcc" />
              </View>
              <View style={styles.matrixVisual}>
                <Animated.View style={[styles.visualCircle, {
                  transform: [{ scale: matrixAnim.interpolate({ inputRange: [0, 1], outputRange: [0.8, 1.2] }) }],
                  opacity: matrixAnim.interpolate({ inputRange: [0, 0.5, 1], outputRange: [0.3, 0.6, 0.3] })
                }]} />
                <Text style={styles.visualText}>CORE ACTIVE</Text>
              </View>
            </View>

            {/* Module Controls */}
            <View style={styles.moduleBar}>
              {Object.keys(modules).map(mod => (
                <TouchableOpacity 
                  key={mod} 
                  style={[styles.moduleItem, modules[mod] ? styles.moduleActive : styles.moduleInactive]}
                  onPress={() => toggleModule(mod)}
                >
                  <Text style={styles.moduleText}>{mod.toUpperCase().substring(0, 3)}</Text>
                  <View style={[styles.moduleDot, { backgroundColor: modules[mod] ? '#00ffcc' : '#444' }]} />
                </TouchableOpacity>
              ))}
            </View>

            {/* Chat Display */}
            <ScrollView 
              ref={scrollRef}
              style={styles.chatArea}
              contentContainerStyle={styles.chatContent}
            >
              {chatLog.map((log, i) => (
                <View key={i} style={[styles.messageWrapper, log.type === 'user' ? styles.userWrapper : styles.angelaWrapper]}>
                  <View style={styles.messageHeader}>
                    <Text style={styles.messageSender}>{log.type === 'user' ? 'COMMANDER' : 'ANGELA'}</Text>
                    <Text style={styles.messageTime}>{new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</Text>
                  </View>
                  <Text style={[styles.messageText, log.type === 'user' ? styles.userText : styles.angelaText]}>
                    {log.type === 'angela' ? '> ' : ''}{log.text}
                  </Text>
                </View>
              ))}
            </ScrollView>

            {/* Input Area */}
            <View style={styles.inputArea}>
              <View style={styles.inputPrefix}>
                <Text style={styles.inputPrefixText}>CMD></Text>
              </View>
              <TextInput
                style={styles.messageInput}
                placeholder="INPUT COMMAND..."
                placeholderTextColor="#444"
                value={message}
                onChangeText={setMessage}
                onSubmitEditing={sendSecureRequest}
              />
              <TouchableOpacity style={styles.sendButton} onPress={sendSecureRequest}>
                <Text style={styles.sendButtonText}>EXE</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </Animated.View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  innerContainer: {
    flex: 1,
    padding: 15,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
    marginBottom: 15,
  },
  headerTitle: {
    color: '#eee',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  headerStatus: {
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  statsContainer: {
    alignItems: 'flex-end',
  },
  statText: {
    color: '#666',
    fontSize: 9,
    fontFamily: 'monospace',
  },
  pairingContainer: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  scannerContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  scannerText: {
    color: '#00ffcc',
    fontSize: 16,
    textAlign: 'center',
    padding: 20,
    backgroundColor: '#000',
    width: '100%',
  },
  cancelButton: {
    padding: 20,
    backgroundColor: '#000',
    width: '100%',
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#ff3366',
    fontSize: 18,
    fontWeight: 'bold',
  },
  qrButton: {
    backgroundColor: '#00ffcc',
    padding: 20,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 20,
  },
  qrButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#333',
  },
  dividerText: {
    color: '#666',
    marginHorizontal: 15,
    fontSize: 12,
  },
  pairingLabel: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 20,
    letterSpacing: 3,
  },
  keyInput: {
    width: '100%',
    height: 50,
    backgroundColor: '#111',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 5,
    color: '#00ffcc',
    paddingHorizontal: 15,
    fontSize: 16,
    fontFamily: 'monospace',
    marginBottom: 20,
  },
  initButton: {
    width: '100%',
    height: 50,
    backgroundColor: '#00ffcc',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 5,
  },
  initButtonText: {
    color: '#000',
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  pairingHint: {
    color: '#666',
    fontSize: 10,
    marginTop: 20,
    textAlign: 'center',
  },
  mainInterface: {
    flex: 1,
  },
  // Matrix Styles
  matrixContainer: {
    flexDirection: 'row',
    backgroundColor: '#0a0a0a',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#1a1a1a',
    height: 120,
  },
  matrixGrid: {
    flex: 1,
    justifyContent: 'center',
  },
  matrixItem: {
    marginBottom: 6,
  },
  matrixLabel: {
    fontSize: 8,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  matrixBarBg: {
    height: 3,
    backgroundColor: '#1a1a1a',
    borderRadius: 1.5,
  },
  matrixBarFill: {
    height: '100%',
    borderRadius: 1.5,
  },
  matrixVisual: {
    width: 80,
    justifyContent: 'center',
    alignItems: 'center',
    borderLeftWidth: 1,
    borderLeftColor: '#1a1a1a',
    marginLeft: 15,
  },
  visualCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#00ffcc',
    position: 'absolute',
  },
  visualText: {
    color: '#00ffcc',
    fontSize: 8,
    fontWeight: 'bold',
    marginTop: 50,
  },
  // Module Styles
  moduleBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  moduleItem: {
    flex: 1,
    marginHorizontal: 4,
    height: 40,
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
  },
  moduleActive: {
    backgroundColor: 'rgba(0, 255, 204, 0.05)',
    borderColor: '#00ffcc',
  },
  moduleInactive: {
    backgroundColor: '#0a0a0a',
    borderColor: '#1a1a1a',
  },
  moduleText: {
    color: '#eee',
    fontSize: 10,
    fontWeight: 'bold',
  },
  moduleDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginTop: 4,
  },
  // Chat Styles
  chatArea: {
    flex: 1,
    backgroundColor: '#0a0a0a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1a1a1a',
    padding: 10,
  },
  chatContent: {
    paddingBottom: 20,
  },
  messageWrapper: {
    marginBottom: 15,
    maxWidth: '90%',
  },
  userWrapper: {
    alignSelf: 'flex-end',
  },
  angelaWrapper: {
    alignSelf: 'flex-start',
  },
  messageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  messageSender: {
    color: '#444',
    fontSize: 8,
    fontWeight: 'bold',
  },
  messageTime: {
    color: '#222',
    fontSize: 8,
    marginLeft: 10,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: '#33ccff',
    textAlign: 'right',
  },
  angelaText: {
    color: '#eee',
    fontFamily: 'monospace',
  },
  // Input Styles
  inputArea: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 15,
    backgroundColor: '#0a0a0a',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1a1a1a',
    paddingHorizontal: 12,
  },
  inputPrefix: {
    marginRight: 8,
  },
  inputPrefixText: {
    color: '#444',
    fontSize: 12,
    fontWeight: 'bold',
  },
  messageInput: {
    flex: 1,
    height: 45,
    color: '#eee',
    fontSize: 14,
  },
  sendButton: {
    paddingHorizontal: 12,
  },
  sendButtonText: {
    color: '#00ffcc',
    fontSize: 12,
    fontWeight: 'bold',
  },
});

export default App;
