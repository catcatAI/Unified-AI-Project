const { spawn } = require('child_process');
const path = require('path');

// Change to the project root directory
const projectRoot = path.join(__dirname, '..');

// Spawn electron process
const electron = spawn('npx', ['electron', '.'], {
  cwd: projectRoot,
  stdio: 'inherit'
});

electron.on('close', (code) => {
  console.log(`Electron process exited with code ${code}`);
});