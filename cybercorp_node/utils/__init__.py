"""CyberCorp Node Utilities Package

This package contains utility classes to reduce code duplication and improve maintainability.
"""

from .cybercorp_client import CyberCorpClient
from .client_manager import ClientManager
from .command_forwarder import CommandForwarder
from .data_persistence import DataPersistence
from .vscode_ui_analyzer import VSCodeUIAnalyzer
from .vscode_automation import VSCodeAutomation
from .response_handler import ResponseHandler

# Import new backend modules if they exist
try:
    from .win32_backend import Win32Backend
except ImportError:
    Win32Backend = None

try:
    from .ocr_backend import OCRBackend
except ImportError:
    OCRBackend = None

try:
    from .vision_model import UIVisionModel
except ImportError:
    UIVisionModel = None

try:
    from .parallel_executor import ParallelExecutor, TaskBuilder
except ImportError:
    ParallelExecutor = None
    TaskBuilder = None

__all__ = [
    'CyberCorpClient',
    'ClientManager',
    'CommandForwarder',
    'DataPersistence',
    'VSCodeUIAnalyzer',
    'VSCodeAutomation',
    'ResponseHandler',
    'Win32Backend',
    'OCRBackend',
    'UIVisionModel',
    'ParallelExecutor',
    'TaskBuilder'
]