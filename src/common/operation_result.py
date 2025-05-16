from dataclasses import dataclass

@dataclass
class OperationResult:
    success: bool
    error: str = None
    data: object = None 