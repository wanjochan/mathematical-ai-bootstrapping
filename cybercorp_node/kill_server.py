import psutil
import sys

pid = int(sys.argv[1]) if len(sys.argv) > 1 else 18732

try:
    proc = psutil.Process(pid)
    proc.terminate()
    print(f"Terminated process {pid}")
except:
    print(f"Process {pid} not found or already terminated")