"""
database.py
-----------
Lightweight in-memory "database" of explosive properties and unit helpers.
No actual database engine is used — just plain Python dicts.

All data sourced from open engineering references and UFC 3-340-02 appendices.
FOR EDUCATIONAL PURPOSES ONLY.
"""

# ---------------------------------------------------------------------------
# Explosive property reference table
# Fields: density (kg/m³), detonation velocity (m/s), VoD reference note
# ---------------------------------------------------------------------------
EXPLOSIVE_PROPERTIES: dict[str, dict] = {
    "TNT": {
        "density_kg_m3":          1630,
        "detonation_velocity_m_s": 6900,
        "gurney_constant_km_s":    2.44,
        "notes": "Trinitrotoluene — the baseline reference explosive.",
    },
    "RDX": {
        "density_kg_m3":          1820,
        "detonation_velocity_m_s": 8750,
        "gurney_constant_km_s":    2.93,
        "notes": "Cyclotrimethylenetrinitramine — more powerful than TNT.",
    },
    "HMX": {
        "density_kg_m3":          1910,
        "detonation_velocity_m_s": 9110,
        "gurney_constant_km_s":    2.97,
        "notes": "Cyclotetramethylenetetranitramine — highest performance here.",
    },
    "C4": {
        "density_kg_m3":          1601,
        "detonation_velocity_m_s": 8050,
        "gurney_constant_km_s":    2.80,
        "notes": "Composition C-4 (≈91% RDX + plasticizer).",
    },
}


def get_explosive_names() -> list[str]:
    """Return sorted list of supported explosive type names."""
    return sorted(EXPLOSIVE_PROPERTIES.keys())


def get_explosive_info(name: str) -> dict:
    """Return the property dict for a given explosive name."""
    if name not in EXPLOSIVE_PROPERTIES:
        raise KeyError(f"Explosive '{name}' not found in database.")
    return EXPLOSIVE_PROPERTIES[name]


# ---------------------------------------------------------------------------
# Unit conversion helpers
# ---------------------------------------------------------------------------

def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462

def lbs_to_kg(lbs: float) -> float:
    """Convert pounds to kilograms."""
    return lbs / 2.20462

def m_to_ft(m: float) -> float:
    """Convert metres to feet."""
    return m * 3.28084

def ft_to_m(ft: float) -> float:
    """Convert feet to metres."""
    return ft / 3.28084

def mm_to_m(mm: float) -> float:
    """Convert millimetres to metres."""
    return mm / 1000.0

def m_to_mm(m: float) -> float:
    """Convert metres to millimetres."""
    return m * 1000.0

def joules_to_ft_lbf(j: float) -> float:
    """Convert Joules to foot-pound-force."""
    return j * 0.737562


# ---------------------------------------------------------------------------
# Saved calculation sessions (in-memory only, lost on exit)
# ---------------------------------------------------------------------------
_session_history: list[dict] = []


def save_session(inputs: dict, results: dict) -> None:
    """Append a calculation session to the in-memory history."""
    _session_history.append({"inputs": inputs, "results": results})


def get_session_history() -> list[dict]:
    """Return the full in-memory session history."""
    return list(_session_history)


def clear_session_history() -> None:
    """Wipe the in-memory session history."""
    _session_history.clear()
