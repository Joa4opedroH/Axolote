from __future__ import annotations


def software_score(mapping_level: int, identification_level: int, music_level: int = 0) -> float:
    """Score from the regulation: Ps = Mp^2 + 8 * sqrt(Id) + 5 * Ms."""
    if not 0 <= mapping_level <= 4:
        raise ValueError("mapping_level must be between 0 and 4")
    if not 0 <= identification_level <= 6:
        raise ValueError("identification_level must be between 0 and 6")
    if music_level not in (0, 1):
        raise ValueError("music_level must be 0 or 1")
    return mapping_level**2 + 8 * (identification_level**0.5) + 5 * music_level
