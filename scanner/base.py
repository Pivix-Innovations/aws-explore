from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .aws_manager import AWSManager

class ServiceScanner(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def service_name(self) -> str:
        """The generic name of the service (e.g., 'ec2')"""
        pass
    
    @property
    @abstractmethod
    def billing_service_name(self) -> str:
        """The name as it appears in Cost Explorer (e.g., 'Amazon Elastic Compute Cloud - Compute')"""
        pass

    @abstractmethod
    def list_resources(self, regions: List[str] = None) -> List[Dict[str, Any]]:
        """
        List active resources for this service.
        :param regions: List of regions where this service is active (detected via billing).
        Returns a list of dicts with keys: 'id', 'name', 'type', 'region', 'url'
        """
        pass

class ScannerFactory:
    _scanners = {}

    @classmethod
    def register(cls, billing_name):
        def decorator(scanner_cls):
            cls._scanners[billing_name] = scanner_cls
            return scanner_cls
        return decorator

    @classmethod
    def get_scanner(cls, billing_name: str):
        scanner_cls = cls._scanners.get(billing_name)
        if scanner_cls:
            return scanner_cls()
        return None

# Import specific scanners here to ensure registration? 
# Or rely on AppConfig.ready() to load them.
