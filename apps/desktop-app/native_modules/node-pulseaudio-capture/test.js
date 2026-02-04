const PulseAudioCapture = require('./index');

async function testPulseAudioCapture() {
    console.log('Testing PulseAudio System Audio Capture...\n');
    
    try {
        const devices = PulseAudioCapture.getDevices();
        console.log('Available Audio Devices:');
        devices.forEach((device, index) => {
            console.log(`  ${index + 1}. ${device.name} (ID: ${device.id})`);
            if (device.description) {
                console.log(`       ${device.description}`);
            }
        });
        
        const defaultDevice = PulseAudioCapture.getDefaultDevice();
        if (defaultDevice) {
            console.log(`\nDefault Device: ${defaultDevice.name}`);
            console.log(`Default Device ID: ${defaultDevice.id}\n`);
        } else {
            console.log('\nNo default device found\n');
        }
        
        const capture = new PulseAudioCapture();
        
        console.log('Starting capture...');
        let sampleCount = 0;
        
        await capture.start(null, (samples) => {
            sampleCount += samples.length;
            const level = samples.reduce((acc, val) => acc + Math.abs(val), 0) / samples.length;
            
            if (sampleCount % 4800 === 0) {
                console.log(`Received samples: ${samples.length}, Level: ${level.toFixed(6)}`);
            }
            
            if (sampleCount >= 48000) {
                console.log(`\nTotal samples received: ${sampleCount}`);
                capture.stop().then(() => {
                    console.log('Capture stopped successfully');
                    process.exit(0);
                });
            }
        });
        
        console.log('Capture started. Listening for system audio...');
        console.log('Press Ctrl+C to stop early\n');
        
    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
}

testPulseAudioCapture();
