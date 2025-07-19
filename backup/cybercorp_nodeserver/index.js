import { WebSocketServer } from 'ws';
import { createServer } from 'http';

class CyberCorpNodeServer {
    constructor(port = 8080) {
        this.port = port;
        this.clients = new Map();
        this.clientIdCounter = 0;
    }

    start() {
        const server = createServer();
        const wss = new WebSocketServer({ server });

        wss.on('connection', (ws, req) => {
            const clientId = ++this.clientIdCounter;
            const clientInfo = {
                id: clientId,
                ws: ws,
                ip: req.socket.remoteAddress,
                connectedAt: new Date(),
                status: 'connected'
            };

            this.clients.set(clientId, clientInfo);
            console.log(`Client ${clientId} connected from ${clientInfo.ip}`);

            ws.on('message', (data) => {
                this.handleMessage(clientId, data);
            });

            ws.on('close', () => {
                console.log(`Client ${clientId} disconnected`);
                this.clients.delete(clientId);
            });

            ws.on('error', (error) => {
                console.error(`Client ${clientId} error:`, error);
            });

            ws.send(JSON.stringify({
                type: 'welcome',
                clientId: clientId,
                message: 'Connected to CyberCorp Node Server'
            }));
        });

        server.listen(this.port, () => {
            console.log(`CyberCorp Node Server listening on port ${this.port}`);
        });
    }

    handleMessage(clientId, data) {
        try {
            const message = JSON.parse(data);
            console.log(`Received from client ${clientId}:`, message);

            switch (message.type) {
                case 'response':
                    this.handleResponse(clientId, message);
                    break;
                case 'heartbeat':
                    this.handleHeartbeat(clientId);
                    break;
                default:
                    console.log(`Unknown message type: ${message.type}`);
            }
        } catch (error) {
            console.error(`Error parsing message from client ${clientId}:`, error);
        }
    }

    handleResponse(clientId, message) {
        console.log(`Response from client ${clientId}:`, message.data);
    }

    handleHeartbeat(clientId) {
        const client = this.clients.get(clientId);
        if (client) {
            client.lastHeartbeat = new Date();
        }
    }

    sendCommand(clientId, command, data = {}) {
        const client = this.clients.get(clientId);
        if (client && client.ws.readyState === 1) {
            const message = {
                type: 'command',
                command: command,
                data: data,
                timestamp: new Date().toISOString()
            };
            client.ws.send(JSON.stringify(message));
            console.log(`Sent command '${command}' to client ${clientId}`);
            return true;
        }
        console.error(`Client ${clientId} not found or not connected`);
        return false;
    }

    broadcast(command, data = {}) {
        let sent = 0;
        this.clients.forEach((client, clientId) => {
            if (this.sendCommand(clientId, command, data)) {
                sent++;
            }
        });
        console.log(`Broadcast command '${command}' to ${sent} clients`);
    }

    getConnectedClients() {
        return Array.from(this.clients.entries()).map(([id, client]) => ({
            id: id,
            ip: client.ip,
            connectedAt: client.connectedAt,
            lastHeartbeat: client.lastHeartbeat
        }));
    }
}

const server = new CyberCorpNodeServer(8080);
server.start();

process.stdin.on('data', (data) => {
    const input = data.toString().trim();
    const parts = input.split(' ');
    const cmd = parts[0];

    switch (cmd) {
        case 'list':
            console.log('Connected clients:', server.getConnectedClients());
            break;
        case 'uia':
            const clientId = parseInt(parts[1]);
            if (clientId) {
                server.sendCommand(clientId, 'get_uia_structure');
            } else {
                server.broadcast('get_uia_structure');
            }
            break;
        case 'process':
            const processClientId = parseInt(parts[1]);
            if (processClientId) {
                server.sendCommand(processClientId, 'get_processes');
            } else {
                server.broadcast('get_processes');
            }
            break;
        case 'exit':
            process.exit(0);
            break;
        default:
            console.log('Commands: list, uia [clientId], process [clientId], exit');
    }
});

console.log('Commands: list, uia [clientId], process [clientId], exit');