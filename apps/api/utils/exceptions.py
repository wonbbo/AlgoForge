"""
API 예외 클래스 정의
"""

from typing import Optional


class AlgoForgeException(Exception):
    """AlgoForge API 기본 예외 클래스"""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatasetNotFoundError(AlgoForgeException):
    """데이터셋을 찾을 수 없는 경우"""
    
    def __init__(self, dataset_id: int):
        super().__init__(
            message=f"Dataset with ID {dataset_id} not found",
            status_code=404,
            details={"dataset_id": dataset_id}
        )


class StrategyNotFoundError(AlgoForgeException):
    """전략을 찾을 수 없는 경우"""
    
    def __init__(self, strategy_id: int):
        super().__init__(
            message=f"Strategy with ID {strategy_id} not found",
            status_code=404,
            details={"strategy_id": strategy_id}
        )


class RunNotFoundError(AlgoForgeException):
    """Run을 찾을 수 없는 경우"""
    
    def __init__(self, run_id: int):
        super().__init__(
            message=f"Run with ID {run_id} not found",
            status_code=404,
            details={"run_id": run_id}
        )


class InvalidDataError(AlgoForgeException):
    """유효하지 않은 데이터인 경우"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=400,
            details=details
        )


class DuplicateDataError(AlgoForgeException):
    """중복 데이터인 경우"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=409,
            details=details
        )


class CancellationRequested(Exception):
    """Run 중지가 요청되었을 때 발생하는 예외"""
    
    def __init__(self, run_id: int):
        self.run_id = run_id
        super().__init__(f"Run {run_id} cancelled by user")
