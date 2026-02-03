const { exec } = require('child_process');

const servicePorts = {
    BACKEND_API: 8000,
    FRONTEND_DASHBOARD: 3000,
    DESKTOP_APP: null, // Electron app, handled separately or doesn't bind a specific port for killing
};

async function killService(serviceName) {
    const port = servicePorts[serviceName];
    if (port === undefined) {
        console.error(`Unknown service: ${serviceName}`);
        process.exit(1);
    }
    if (port === null) {
        console.log(`Service ${serviceName} does not have a fixed port to kill. Skipping.`);
        return;
    }

    console.log(`Attempting to kill process on port ${port} for service: ${serviceName}`);
    // Use fkill-cli as a command-line tool
    exec(`npx fkill ${port}`, (error, stdout, stderr) => {
        if (stdout.includes('No process found')) {
            console.log(`No process found running on port ${port}.`);
        } else if (error) {
            console.error(`Error killing process on port ${port}: ${stderr}`);
            process.exit(1);
        } else {
            console.log(`Successfully killed process on port ${port}.`);
        }
    });
}

async function main() {
    const args = process.argv.slice(2); // Skip 'node' and 'script_name.js'

    if (args.length < 2 || args[0] !== 'kill-service') {
        console.error('Usage: node port_manager.js kill-service <SERVICE_NAME>');
        process.exit(1);
    }

    const serviceName = args[1];
    await killService(serviceName);
}

main();