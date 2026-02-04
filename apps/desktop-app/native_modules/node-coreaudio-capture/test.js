const CoreAudioCapture = require('./index');

async function testCoreAudioCapture() {
    console.log('Testing CoreAudio System Audio Capture...\n');
    
    try {
        const devices = CoreAudioCapture.getDevices();
        console.log('Available Audio Devices:');
        devices.forEach((device, index) => {
            console.log(`  ${index + 1}. ${device.name} (ID: ${device.id})`);
        });
        
        const defaultDevice = CoreAudioCapture.getDefaultDevice();
        console.log(`\nDefault Device: ${defaultDevice.name}`);
        console.log(`Default Device ID: ${defaultDevice.id}\n`);
        
        const capture = new CoreAudioCapture();
        
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

testCoreAudioCapture();
