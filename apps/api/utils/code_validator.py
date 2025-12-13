"""
코드 검증기 - 커스텀 지표 코드 보안 검증

사용자가 제공한 Python 코드를 실행하기 전에 기본적인 보안 검증을 수행합니다.
개인 사용 MVP이므로 기본 수준의 검증만 수행하며, 프로덕션 환경에서는
더 엄격한 샌드박스 환경이 필요합니다.
"""

import ast
from typing import List, Tuple


# 금지된 키워드 목록
DANGEROUS_KEYWORDS = [
    'import os',
    'import sys', 
    'import subprocess',
    'import shutil',
    'import socket',
    'import urllib',
    'import requests',
    'eval',
    'exec',
    '__import__',
    'open(',
    'file(',
    'input(',
    'raw_input',
    'compile(',
    'globals(',
    'locals(',
    'vars(',
    'dir(',
    'delattr',
    'setattr',
]

# 허용된 import 목록
ALLOWED_IMPORTS = [
    'pandas',
    'pd',
    'numpy',
    'np',
    'ta',
    'typing',
    'Dict',
    'Any',
    'List',
]


def validate_indicator_code(code: str) -> Tuple[bool, str, List[str]]:
    """
    지표 코드 기본 검증
    
    Args:
        code: Python 함수 코드
    
    Returns:
        Tuple[bool, str, List[str]]: (검증 통과 여부, 메시지, 에러 목록)
    
    검증 항목:
        1. 위험 키워드 체크
        2. AST 파싱 (구문 검증)
        3. 함수 정의 확인
        4. 함수 시그니처 확인 (2개 인자)
        5. import 문 검증
    """
    errors = []
    
    # 1. 위험 키워드 체크
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in code:
            errors.append(f"금지된 키워드가 포함되어 있습니다: '{keyword}'")
    
    # 2. AST 파싱 (구문 검증)
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        errors.append(f"구문 오류: {str(e)}")
        return False, "코드 검증 실패", errors
    
    # 3. 함수 정의 확인
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    
    if len(functions) == 0:
        errors.append("함수 정의가 없습니다. 최소 하나의 함수를 정의해야 합니다.")
        return False, "코드 검증 실패", errors
    
    if len(functions) > 1:
        errors.append(
            f"함수가 {len(functions)}개 정의되어 있습니다. "
            "정확히 하나의 함수만 정의해야 합니다."
        )
        return False, "코드 검증 실패", errors
    
    # 4. 함수 시그니처 확인
    func = functions[0]
    
    # 인자 개수 확인 (df, params 두 개)
    if len(func.args.args) != 2:
        errors.append(
            f"함수는 정확히 2개의 인자(df, params)를 받아야 합니다. "
            f"현재 인자 개수: {len(func.args.args)}"
        )
    
    # 5. import 문 검증
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    
    for imp in imports:
        if isinstance(imp, ast.Import):
            for alias in imp.names:
                module_name = alias.name.split('.')[0]
                if module_name not in ALLOWED_IMPORTS:
                    errors.append(
                        f"허용되지 않은 모듈 import: '{alias.name}'. "
                        f"허용된 모듈: {', '.join(ALLOWED_IMPORTS)}"
                    )
        
        elif isinstance(imp, ast.ImportFrom):
            if imp.module:
                module_name = imp.module.split('.')[0]
                if module_name not in ALLOWED_IMPORTS:
                    errors.append(
                        f"허용되지 않은 모듈 import: 'from {imp.module}'. "
                        f"허용된 모듈: {', '.join(ALLOWED_IMPORTS)}"
                    )
    
    # 검증 결과 반환
    if errors:
        return False, "코드 검증 실패", errors
    
    return True, "코드 검증 통과", []


def validate_indicator_code_simple(code: str) -> None:
    """
    지표 코드 간단 검증 (예외 발생 버전)
    
    Args:
        code: Python 함수 코드
    
    Raises:
        ValueError: 검증 실패 시
    """
    is_valid, message, errors = validate_indicator_code(code)
    
    if not is_valid:
        error_details = "\n".join(f"  - {err}" for err in errors)
        raise ValueError(f"{message}:\n{error_details}")


def extract_function_name(code: str) -> str:
    """
    코드에서 함수 이름 추출
    
    Args:
        code: Python 함수 코드
    
    Returns:
        str: 함수 이름
    
    Raises:
        ValueError: 함수를 찾을 수 없는 경우
    """
    try:
        tree = ast.parse(code)
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        
        if not functions:
            raise ValueError("함수 정의를 찾을 수 없습니다")
        
        return functions[0].name
        
    except SyntaxError as e:
        raise ValueError(f"구문 오류: {str(e)}")

