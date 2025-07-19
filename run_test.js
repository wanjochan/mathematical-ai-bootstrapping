import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';

async function runTest() {
    console.log('Starting CyberCorp test to capture VSCode window structure...\n');

    // Start server
    console.log('1. Starting server...');
    const server = spawn('node', ['cybercorp_nodeserver/index.js'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
    });

    let serverOutput = '';
    let clientOutput = '';

    server.stdout.on('data', (data) => {
        const output = data.toString();
        serverOutput += output;
        console.log(`[SERVER] ${output.trim()}`);
    });

    server.stderr.on('data', (data) => {
        console.error(`[SERVER ERROR] ${data.toString().trim()}`);
    });

    // Wait for server to start
    await setTimeout(2000);

    // Start client
    console.log('\n2. Starting client...');
    const client = spawn('node', ['cybercorp_node/index.js'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
    });

    client.stdout.on('data', (data) => {
        const output = data.toString();
        clientOutput += output;
        console.log(`[CLIENT] ${output.trim()}`);
    });

    client.stderr.on('data', (data) => {
        console.error(`[CLIENT ERROR] ${data.toString().trim()}`);
    });

    // Wait for client to connect
    await setTimeout(3000);

    // Test commands
    console.log('\n3. Testing commands...');
    
    console.log('\n- Listing connected clients:');
    server.stdin.write('list\n');
    await setTimeout(1000);

    console.log('\n- Getting UIA structure (this will capture the active window):');
    console.log('  (Make sure VSCode is the active window for best results)');
    server.stdin.write('uia 1\n');
    await setTimeout(5000);

    console.log('\n- Getting process information:');
    server.stdin.write('process 1\n');
    await setTimeout(3000);

    // Clean up
    console.log('\n4. Cleaning up...');
    client.kill();
    server.stdin.write('exit\n');
    
    await setTimeout(1000);
    server.kill();

    console.log('\nTest completed!');
}

// Give user time to make VSCode the active window
console.log('This test will capture the UIA structure of the active window.');
console.log('Please make VSCode the active window within the next 5 seconds...');
global.setTimeout(() => {
    runTest().catch(console.error);
}, 5000);