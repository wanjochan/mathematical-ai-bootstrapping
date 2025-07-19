import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';

async function runTest() {
    console.log('Starting CyberCorp test...\n');

    console.log('1. Starting server...');
    const server = spawn('node', ['cybercorp_nodeserver/index.js'], {
        stdio: ['pipe', 'pipe', 'pipe']
    });

    server.stdout.on('data', (data) => {
        console.log(`[SERVER] ${data.toString().trim()}`);
    });

    server.stderr.on('data', (data) => {
        console.error(`[SERVER ERROR] ${data.toString().trim()}`);
    });

    await setTimeout(2000);

    console.log('\n2. Starting client...');
    const client = spawn('node', ['cybercorp_node/index.js'], {
        stdio: ['pipe', 'pipe', 'pipe']
    });

    client.stdout.on('data', (data) => {
        console.log(`[CLIENT] ${data.toString().trim()}`);
    });

    client.stderr.on('data', (data) => {
        console.error(`[CLIENT ERROR] ${data.toString().trim()}`);
    });

    await setTimeout(3000);

    console.log('\n3. Testing commands...');
    
    console.log('\n- Listing connected clients:');
    server.stdin.write('list\n');
    await setTimeout(1000);

    console.log('\n- Getting UIA structure:');
    server.stdin.write('uia 1\n');
    await setTimeout(3000);

    console.log('\n- Getting process information:');
    server.stdin.write('process 1\n');
    await setTimeout(3000);

    console.log('\n4. Cleaning up...');
    client.kill();
    server.stdin.write('exit\n');
    
    await setTimeout(1000);
    server.kill();

    console.log('\nTest completed!');
}

runTest().catch(console.error);