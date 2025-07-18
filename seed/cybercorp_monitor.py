"""
CyberCorp 简易中控系统

监控员工进程并提供基本状态报告的简单脚本。
"""
import psutil
import time
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cybercorp_monitor.log')
    ]
)
logger = logging.getLogger('CyberCorp监控器')

class CyberCorpMonitor:
    def __init__(self):
        """初始化中控系统"""
        self.employees = {}
        self.process_stats = {}
        self.last_report_time = datetime.now()
        logger.info("CyberCorp中控系统启动")
        
    def add_employee(self, employee_id, name, process_name):
        """添加需要监控的员工"""
        self.employees[employee_id] = {
            'id': employee_id,
            'name': name,
            'process_name': process_name,
            'status': 'unknown'
        }
        logger.info(f"添加员工: ID={employee_id}, 名称={name}, 进程={process_name}")
        
    def monitor_processes(self):
        """监控所有员工关联的进程"""
        for emp_id, emp_info in self.employees.items():
            process_name = emp_info['process_name']
            found = False
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                if process_name.lower() in proc.info['name'].lower():
                    # 进程找到了，更新状态
                    memory_mb = proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0
                    self.process_stats[emp_id] = {
                        'timestamp': datetime.now().isoformat(),
                        'pid': proc.pid,
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': round(memory_mb, 2),
                        'status': 'running'
                    }
                    self.employees[emp_id]['status'] = 'active'
                    found = True
                    break
            
            if not found:
                # 进程没找到
                self.employees[emp_id]['status'] = 'inactive'
                if emp_id in self.process_stats:
                    self.process_stats[emp_id]['status'] = 'stopped'
        
        return self.process_stats
    
    def generate_report(self):
        """生成状态报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'employees': self.employees,
            'processes': self.process_stats
        }
        self.last_report_time = datetime.now()
        return report
    
    def print_status(self):
        """打印当前状态"""
        stats = self.monitor_processes()
        logger.info(f"{'='*50}")
        logger.info(f"CyberCorp状态报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*50}")
        
        for emp_id, emp_info in self.employees.items():
            logger.info(f"员工: {emp_info['name']} (ID: {emp_id})")
            logger.info(f"  状态: {emp_info['status']}")
            
            if emp_id in stats and stats[emp_id]['status'] == 'running':
                proc_stat = stats[emp_id]
                logger.info(f"  PID: {proc_stat['pid']}")
                logger.info(f"  CPU: {proc_stat['cpu_percent']}%")
                logger.info(f"  内存: {proc_stat['memory_mb']} MB")
            
            logger.info("")
        
        return stats

def main():
    """主函数"""
    monitor = CyberCorpMonitor()
    
    # 添加员工一号 (VSCode+Augment)
    monitor.add_employee('emp001', '员工一号', 'Code.exe')
    
    try:
        logger.info("开始监控进程，按Ctrl+C退出...")
        while True:
            monitor.print_status()
            time.sleep(5)  # 每5秒更新一次
    except KeyboardInterrupt:
        logger.info("监控被用户中断")
    finally:
        logger.info("生成最终报告")
        final_report = monitor.generate_report()
        
        # 将最终报告保存为JSON
        with open('cybercorp_report.json', 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        logger.info("报告已保存至cybercorp_report.json")
        logger.info("CyberCorp中控系统关闭")

if __name__ == "__main__":
    main()
