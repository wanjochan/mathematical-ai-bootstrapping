// 实时系统监控仪表盘
class SystemMonitor {
    constructor() {
        this.eventSource = null;
        this.performanceChart = null;
        this.networkChart = null;
        this.metricsData = [];
        this.charts = {};
        this.init();
    }

    init() {
        this.setupCharts();
        this.connectSSE();
        this.updateTime();
        this.startPeriodicUpdates();
    }

    setupCharts() {
        // 性能趋势图
        const perfCtx = document.getElementById('performance-chart').getContext('2d');
        this.performanceChart = new Chart(perfCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU %',
                    data: [],
                    borderColor: '#32c659',
                    backgroundColor: 'rgba(50, 198, 89, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Memory %',
                    data: [],
                    borderColor: '#ffa726',
                    backgroundColor: 'rgba(255, 167, 38, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: this.getChartOptions('系统性能趋势')
        });

        // 网络流量图
        const networkCtx = document.getElementById('network-chart').getContext('2d');
        this.networkChart = new Chart(networkCtx, {
            type: 'doughnut',
            data: {
                labels: ['已用', '可用'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#ff5252', '#32c659'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e1e8ed',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    getChartOptions(title) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#e1e8ed',
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#8899a6' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    ticks: { 
                        color: '#8899a6',
                        callback: value => value + '%'
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            elements: {
                point: { radius: 0 },
                line: { borderWidth: 2 }
            }
        };
    }

    connectSSE() {
        this.eventSource = new EventSource('/dashboard/events');
        
        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateMetrics(data);
            this.updateCharts(data);
        };

        this.eventSource.onerror = (error) => {
            console.log('SSE连接错误:', error);
            setTimeout(() => this.connectSSE(), 5000);
        };
    }

    updateMetrics(data) {
        // 更新主指标
        this.animateValue('cpu-value', parseFloat(data.cpu), '%');
        this.animateValue('memory-value', data.memory_percent, '%');
        this.animateValue('disk-value', Math.round((data.disk_used / data.disk_total) * 100), '%');
        this.animateUptime(data.uptime);
        
        // 更新进度条
        this.updateProgressBar('cpu-progress', parseFloat(data.cpu));
        this.updateProgressBar('memory-progress', data.memory_percent);
        this.updateProgressBar('disk-progress', (data.disk_used / data.disk_total) * 100);

        // 更新进程数量
        document.getElementById('process-count').textContent = `${data.processes} 个进程`;
    }

    animateValue(elementId, newValue, suffix = '') {
        const element = document.getElementById(elementId);
        const currentValue = parseFloat(element.textContent) || 0;
        const delta = newValue - currentValue;
        const duration = 1000;
        const steps = 60;
        let currentStep = 0;

        if (Math.abs(delta) < 0.1) return;

        const step = () => {
            currentStep++;
            const progress = currentStep / steps;
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = currentValue + (delta * eased);
            element.textContent = Math.round(value) + suffix;

            if (currentStep < steps) {
                requestAnimationFrame(step);
            }
        };

        requestAnimationFrame(step);
    }

    updateProgressBar(elementId, value) {
        const bar = document.getElementById(elementId);
        bar.style.width = `${Math.min(value, 100)}%`;
    }

    animateUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        const formatted = 
            `${hours.toString().padStart(2, '0')}:` +
            `${minutes.toString().padStart(2, '0')}:` +
            `${secs.toString().padStart(2, '0')}`;
            
        document.getElementById('uptime-value').textContent = formatted;
    }

    updateCharts(data) {
        const now = new Date().toLocaleTimeString();
        
        // 更新性能图表
        if (this.performanceChart.data.labels.length > 20) {
            this.performanceChart.data.labels.shift();
            this.performanceChart.data.datasets[0].data.shift();
            this.performanceChart.data.datasets[1].data.shift();
        }

        this.performanceChart.data.labels.push(now);
        this.performanceChart.data.datasets[0].data.push(data.cpu);
        this.performanceChart.data.datasets[1].data.push(data.memory_percent);
        this.performanceChart.update('none');

        // 更新网络图表
        const diskUsed = Math.round((data.disk_used / data.disk_total) * 100);
        this.networkChart.data.datasets[0].data = [diskUsed, 100 - diskUsed];
        this.networkChart.update('none');
    }

    updateTime() {
        setInterval(() => {
            const now = new Date().toLocaleString('zh-CN');
            document.getElementById('current-time').textContent = now;
        }, 1000);
    }

    startPeriodicUpdates() {
        // 每隔30秒获取任务状态
        setInterval(async () => {
            try {
                const response = await fetch('/api/v1/tasks');
                const tasks = await response.json();
                this.updateTasks(tasks);
            } catch (error) {
                console.log('无法加载任务数据:', error);
            }
        }, 30000);

        // 立即获取一次任务数据
        this.fetchInitialData();
    }

    async fetchInitialData() {
        try {
            const [tasksResponse, employeesResponse] = await Promise.all([
                fetch('/api/v1/tasks'),
                fetch('/api/v1/employees')
            ]);

            const tasks = await tasksResponse.json();
            const employees = await employeesResponse.json();
            
            this.updateTasks(tasks);
            this.updateEmployees(employees);
        } catch (error) {
            console.log('初始数据加载失败:', error);
        }
    }

    updateTasks(tasks) {
        const container = document.getElementById('tasks-list');
        
        if (!tasks || tasks.length === 0) {
            container.innerHTML = `
                <div class="task-item">
                    <span class="task-status-icon">✅</span>
                    <span>没有正在进行的任务</span>
                </div>
            `;
            return;
        }

        container.innerHTML = tasks.slice(0, 5).map(task => `
            <div class="task-item" data-task-id="${task.id}">
                <div class="task-header">
                    <span class="task-name">${task.name}</span>
                    <span class="task-status status-${task.status}">${task.status}</span>
                </div>
                <div class="task-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${task.progress || 0}%"></div>
                    </div>
                    <span class="progress-text">${task.progress || 0}%</span>
                </div>
            </div>
        `).join('');
    }

    updateEmployees(employees) {
        // TODO: 实现员工状态显示
        console.log('员工数据:', employees);
    }
}

// 初始化监控系统
document.addEventListener('DOMContentLoaded', () => {
    window.systemMonitor = new SystemMonitor();
});

// 页面卸载时清理资源
window.addEventListener('beforeunload', () => {
    if (window.systemMonitor && window.systemMonitor.eventSource) {
        window.systemMonitor.eventSource.close();
    }
});