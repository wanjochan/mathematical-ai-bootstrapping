import WebSocket from 'ws';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

class CyberCorpNode {
    constructor(serverUrl = 'ws://localhost:8080') {
        this.serverUrl = serverUrl;
        this.ws = null;
        this.clientId = null;
        this.reconnectInterval = 5000;
        this.heartbeatInterval = 30000;
    }

    connect() {
        console.log(`Connecting to ${this.serverUrl}...`);
        this.ws = new WebSocket(this.serverUrl);

        this.ws.on('open', () => {
            console.log('Connected to server');
            this.startHeartbeat();
        });

        this.ws.on('message', (data) => {
            this.handleMessage(data);
        });

        this.ws.on('close', () => {
            console.log('Disconnected from server');
            this.stopHeartbeat();
            setTimeout(() => this.connect(), this.reconnectInterval);
        });

        this.ws.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
    }

    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            console.log('Received:', message);

            switch (message.type) {
                case 'welcome':
                    this.clientId = message.clientId;
                    console.log(`Assigned client ID: ${this.clientId}`);
                    break;
                case 'command':
                    this.handleCommand(message.command, message.data);
                    break;
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    async handleCommand(command, data) {
        console.log(`Executing command: ${command}`);
        
        switch (command) {
            case 'get_uia_structure':
                await this.getUIAStructure();
                break;
            case 'get_processes':
                await this.getProcesses();
                break;
            default:
                console.log(`Unknown command: ${command}`);
        }
    }

    async getUIAStructure() {
        try {
            const powershellScript = `
Add-Type @"
using System;
using System.Collections.Generic;
using System.Windows.Automation;
using System.Runtime.InteropServices;
using System.Text;

public class UIAHelper {
    public static string GetWindowStructure() {
        StringBuilder result = new StringBuilder();
        
        // First try to get VSCode window
        try {
            AutomationElement desktop = AutomationElement.RootElement;
            Condition vscodeCondition = new PropertyCondition(
                AutomationElement.ClassNameProperty, 
                "Chrome_WidgetWin_1"
            );
            
            AutomationElementCollection windows = desktop.FindAll(
                TreeScope.Children, 
                vscodeCondition
            );
            
            foreach (AutomationElement window in windows) {
                string name = window.Current.Name;
                if (name.Contains("Visual Studio Code") || name.Contains("VSCode")) {
                    result.AppendLine("=== Found VSCode Window ===");
                    result.AppendLine("Window: " + name);
                    result.AppendLine(GetElementInfo(window, 0, 10));
                    result.AppendLine();
                }
            }
        } catch { }
        
        // Also get active window
        try {
            IntPtr hwnd = GetForegroundWindow();
            AutomationElement activeElement = AutomationElement.FromHandle(hwnd);
            result.AppendLine("=== Active Window ===");
            result.AppendLine("Window: " + activeElement.Current.Name);
            result.AppendLine(GetElementInfo(activeElement, 0, 10));
        } catch (Exception ex) {
            result.AppendLine("Error getting active window: " + ex.Message);
        }
        
        return result.ToString();
    }
    
    private static string GetElementInfo(AutomationElement element, int depth, int maxDepth) {
        if (element == null || depth > maxDepth) return "";
        
        StringBuilder info = new StringBuilder();
        string indent = new string(' ', depth * 2);
        
        string controlType = element.Current.ControlType.ProgrammaticName.Replace("ControlType.", "");
        string name = element.Current.Name;
        string className = element.Current.ClassName;
        string automationId = element.Current.AutomationId;
        
        info.Append(indent + "- " + controlType);
        if (!string.IsNullOrEmpty(name)) info.Append(" [" + name + "]");
        if (!string.IsNullOrEmpty(className)) info.Append(" (" + className + ")");
        if (!string.IsNullOrEmpty(automationId)) info.Append(" #" + automationId);
        info.AppendLine();
        
        try {
            AutomationElementCollection children = element.FindAll(
                TreeScope.Children, 
                System.Windows.Automation.Condition.TrueCondition
            );
            
            foreach (AutomationElement child in children) {
                info.Append(GetElementInfo(child, depth + 1, maxDepth));
            }
        } catch { }
        
        return info.ToString();
    }
    
    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();
}
"@ -ReferencedAssemblies System.Windows.Forms, UIAutomationClient, UIAutomationTypes

[UIAHelper]::GetWindowStructure()
`;

            const { stdout, stderr } = await execAsync(`powershell -ExecutionPolicy Bypass -Command "${powershellScript.replace(/"/g, '\\"').replace(/\n/g, ' ')}"`, {
                maxBuffer: 1024 * 1024 * 10
            });

            if (stderr) {
                console.error('PowerShell error:', stderr);
            }

            this.sendResponse('uia_structure', {
                structure: stdout || 'No UIA structure found',
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('Error getting UIA structure:', error);
            this.sendResponse('uia_structure', {
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    async getProcesses() {
        try {
            const { stdout, stderr } = await execAsync('powershell -Command "Get-Process | Select-Object Id, ProcessName, CPU, WorkingSet | ConvertTo-Json"', {
                maxBuffer: 1024 * 1024 * 10
            });

            if (stderr) {
                console.error('PowerShell error:', stderr);
            }

            const processes = JSON.parse(stdout);
            const topProcesses = processes
                .sort((a, b) => (b.WorkingSet || 0) - (a.WorkingSet || 0))
                .slice(0, 20)
                .map(p => ({
                    id: p.Id,
                    name: p.ProcessName,
                    cpu: p.CPU || 0,
                    memory: Math.round((p.WorkingSet || 0) / 1024 / 1024)
                }));

            this.sendResponse('processes', {
                processes: topProcesses,
                total: processes.length,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('Error getting processes:', error);
            this.sendResponse('processes', {
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    sendResponse(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'response',
                responseType: type,
                data: data,
                clientId: this.clientId
            };
            this.ws.send(JSON.stringify(message));
            console.log(`Sent ${type} response`);
        }
    }

    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'heartbeat' }));
            }
        }, this.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
}

const client = new CyberCorpNode();
client.connect();

console.log('CyberCorp Node Client started');
console.log('Press Ctrl+C to exit');