"""
차트 관련 유틸리티 함수
"""


def generate_color_from_field(field: str) -> str:
    """
    필드명을 기반으로 결정적인 색상 생성
    
    같은 필드명은 항상 같은 색상을 반환하지만, 다른 필드명은 다른 색상을 반환합니다.
    결정적(deterministic)이지만 시각적으로 구분 가능한 색상을 생성합니다.
    
    Args:
        field: 필드명
        
    Returns:
        HEX 색상 코드 (예: "#2962FF")
    """
    # 필드명을 해시하여 색상 생성
    hash_value = hash(field)
    
    # 음수 방지
    hash_value = abs(hash_value)
    
    # HSL 색상 공간 사용
    hue = hash_value % 360
    saturation = 60 + (hash_value % 20)  # 60-80%
    lightness = 45 + (hash_value % 15)  # 45-60%
    
    # HSL을 RGB로 변환
    def hsl_to_rgb(h, s, l):
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        
        if s == 0:
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1/6:
                    return p + (q - p) * 6 * t
                if t < 1/2:
                    return q
                if t < 2/3:
                    return p + (q - p) * (2/3 - t) * 6
                return p
            
            if l < 0.5:
                q = l * (1 + s)
            else:
                q = l + s - l * s
            p = 2 * l - q
            
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return int(r * 255), int(g * 255), int(b * 255)
    
    r, g, b = hsl_to_rgb(hue, saturation, lightness)
    
    # HEX로 변환
    return f"#{r:02x}{g:02x}{b:02x}"

