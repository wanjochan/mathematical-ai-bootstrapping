"""
CyberCorp Client Windows Service
Runs the client as a Windows service with auto-restart capability
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess
import time
import logging
import threading

# Setup logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'client_service.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CyberCorpClientService')

class CyberCorpClientService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CyberCorpClient"
    _svc_display_name_ = "CyberCorp Control Client"
    _svc_description_ = "CyberCorp control client that connects to the control server"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        self.monitor_thread = None
        self.running = True
        
    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        logger.info("Service stop requested")
        
        self.running = False
        win32event.SetEvent(self.stop_event)
        
        # Stop the client process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        
        # Wait for monitor thread
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        logger.info("Service stopped")
        
    def SvcDoRun(self):
        """Main service loop"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        logger.info("Service started")
        self.main()
        
    def main(self):
        """Service main logic"""
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self.monitor_client)
        self.monitor_thread.start()
        
        # Wait for stop signal
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        
    def monitor_client(self):
        """Monitor and restart client as needed"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        watchdog_script = os.path.join(script_dir, 'client_watchdog.py')
        
        restart_count = 0
        max_quick_restarts = 5
        quick_restart_window = 300  # 5 minutes
        restart_times = []
        
        while self.running:
            try:
                # Clean old restart times
                current_time = time.time()
                restart_times = [t for t in restart_times if current_time - t < quick_restart_window]
                
                # Check if too many quick restarts
                if len(restart_times) >= max_quick_restarts:
                    logger.error(f"Too many restarts ({max_quick_restarts}) in {quick_restart_window}s")
                    logger.error("Service stopping to prevent crash loop")
                    break
                
                logger.info(f"Starting client watchdog (attempt #{restart_count + 1})")
                
                # Start the watchdog which will manage the client
                self.process = subprocess.Popen(
                    [sys.executable, watchdog_script],
                    cwd=script_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                restart_times.append(time.time())
                restart_count += 1
                
                # Monitor watchdog output
                while self.running and self.process.poll() is None:
                    if self.process.stdout:
                        line = self.process.stdout.readline()
                        if line:
                            logger.info(f"[WATCHDOG] {line.strip()}")
                    time.sleep(0.1)
                
                if self.process.poll() is not None:
                    exit_code = self.process.returncode
                    logger.warning(f"Watchdog exited with code: {exit_code}")
                    
                    if self.running:
                        # Wait before restart
                        logger.info("Restarting watchdog in 10 seconds...")
                        time.sleep(10)
                        
            except Exception as e:
                logger.error(f"Error in monitor thread: {e}")
                time.sleep(10)
                
        logger.info("Monitor thread stopped")

def install_service():
    """Install the service"""
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CyberCorpClientService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(CyberCorpClientService)

if __name__ == '__main__':
    install_service()