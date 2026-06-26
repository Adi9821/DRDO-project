"""
calculations.py
---------------
Implements fragmentation formulas from UFC 3-340-02
(Unified Facilities Criteria: Structures to Resist the Effects of Accidental Explosions).

All calculations are for EDUCATIONAL PURPOSES ONLY.
"""

import math
import numpy as np


# ---------------------------------------------------------------------------
# Gurney Energy Constants (sqrt(2E)) in km/s
# Source: UFC 3-340-02, Table 2-6
# These represent the specific energy released by each explosive type.
# ---------------------------------------------------------------------------
GURNEY_CONSTANTS = {
    "TNT":  2.44,   # km/s
    "RDX":  2.93,   # km/s
    "HMX":  2.97,   # km/s
    "C4":   2.80,   # km/s (similar to RDX-based compositions)
}

# Mott scaling constant B (material-dependent).
# For steel casings, a commonly used value is ~0.3 (in SI-consistent units).
# UFC 3-340-02 and Mott's original work use empirical fits; we use a
# representative steel value here.
MOTT_B_STEEL = 0.30  # dimensionless (for SI units: kg, m)


def gurney_velocity(explosive_type: str, charge_weight_kg: float,
                    casing_weight_kg: float) -> float:
    """
    Compute the initial fragment velocity using the Gurney equation
    for a cylindrical casing (UFC 3-340-02, Section 2-14.5).

    Formula (cylindrical geometry):
        V0 = sqrt(2E) * sqrt(M/C / (1 + M/C / 2))^(-1)

    Simplified form often written as:
        V0 = sqrt(2E) / sqrt(M/C + 0.5)

    where:
        sqrt(2E) = Gurney energy constant for the explosive [km/s]
        M        = casing (metal) mass [kg]
        C        = charge (explosive) mass [kg]

    Returns:
        V0 in m/s
    """
    if explosive_type not in GURNEY_CONSTANTS:
        raise ValueError(f"Unknown explosive type: {explosive_type}")
    if charge_weight_kg <= 0 or casing_weight_kg <= 0:
        raise ValueError("Charge weight and casing weight must be > 0.")

    sqrt_2E = GURNEY_CONSTANTS[explosive_type]  # km/s
    ratio = casing_weight_kg / charge_weight_kg  # M/C (dimensionless)

    # Gurney velocity (km/s) → convert to m/s
    V0_km_s = sqrt_2E / math.sqrt(ratio + 0.5)
    return V0_km_s * 1000.0  # m/s


def mott_fragment_distribution(casing_weight_kg: float,
                                casing_thickness_m: float,
                                casing_diameter_m: float,
                                charge_weight_kg: float
                                ) -> tuple[float, float, np.ndarray, np.ndarray]:
    """
    Compute fragment mass distribution using the Mott equation
    (UFC 3-340-02, Equation 2-8).

    The Mott distribution gives the number of fragments with mass >= m:
        N(m) = N_total * exp(-(m / m_avg)^0.5)

    where:
        m_avg  = average fragment mass (Mott scaling) [kg]
        N_total = total number of fragments

    Mott characteristic mass parameter (MA):
        MA = B * t^(5/6) * d_i^(1/3) * (1 + t/d_i)

    where:
        B    = Mott material constant for steel (~0.30 in SI)
        t    = casing wall thickness [m]
        d_i  = inner diameter of casing [m] ≈ outer diameter − 2*t

    Returns:
        (m_avg_kg, largest_fragment_kg, mass_bins, cumulative_counts)
    """
    if casing_thickness_m <= 0 or casing_diameter_m <= 0:
        raise ValueError("Casing thickness and diameter must be > 0.")
    if casing_thickness_m >= casing_diameter_m / 2:
        raise ValueError("Casing thickness must be less than casing radius.")

    t  = casing_thickness_m
    d_i = max(casing_diameter_m - 2 * t, 1e-6)   # inner diameter [m]

    # Mott characteristic mass (MA) — controls average fragment size
    # Units: t in [m], d_i in [m], MA in [kg]
    MA = MOTT_B_STEEL * (t ** (5 / 6)) * (d_i ** (1 / 3)) * (1 + t / d_i)

    # Average fragment mass [kg]
    m_avg = 2 * MA ** 2   # Mott distribution mean

    # Total number of fragments (mass conservation approximation)
    N_total = max(int(casing_weight_kg / m_avg), 1)

    # Largest fragment: 1/N_total of the distribution tail
    # Derived from N(m_max) = 1:
    #   1 = N_total * exp(-(m_max / m_avg)^0.5)
    #   m_max = m_avg * (ln(N_total))^2
    if N_total > 1:
        m_largest = m_avg * (math.log(N_total) ** 2)
    else:
        m_largest = m_avg

    # Build a cumulative fragment count curve over a mass range
    m_min = m_avg * 0.001
    m_max_plot = m_largest * 1.2
    mass_bins = np.linspace(m_min, m_max_plot, 300)

    # N(m) = N_total * exp(-(m/m_avg)^0.5)
    cumulative_counts = N_total * np.exp(-np.sqrt(mass_bins / m_avg))

    return m_avg, m_largest, mass_bins, cumulative_counts


def fragment_velocity_at_distance(V0_m_s: float, distance_m: float,
                                   fragment_mass_kg: float,
                                   drag_coefficient: float = 0.47,
                                   air_density: float = 1.225,
                                   fragment_area_m2: float | None = None
                                   ) -> float:
    """
    Compute fragment velocity at a given standoff distance using
    ballistic drag retardation (UFC 3-340-02, Section 2-14.7):

        V(x) = V0 * exp(-Cd * rho_air * A * x / (2 * m))

    where:
        V0            = initial fragment velocity [m/s]
        x             = distance from explosion [m]
        Cd            = drag coefficient (≈0.47 for a sphere)
        rho_air       = air density [kg/m³] (≈1.225 at sea level)
        A             = fragment presented area [m²]
        m             = fragment mass [kg]

    Fragment area is estimated from mass assuming a spherical steel fragment:
        rho_steel = 7850 kg/m³
        r = (3m / (4π*rho_steel))^(1/3)
        A = π * r²

    Returns:
        V(x) in m/s
    """
    if distance_m < 0:
        raise ValueError("Distance must be ≥ 0.")
    if V0_m_s <= 0:
        raise ValueError("Initial velocity must be > 0.")
    if fragment_mass_kg <= 0:
        raise ValueError("Fragment mass must be > 0.")

    if fragment_area_m2 is None:
        # Estimate cross-sectional area assuming a spherical steel fragment
        rho_steel = 7850.0  # kg/m³
        radius = (3 * fragment_mass_kg / (4 * math.pi * rho_steel)) ** (1 / 3)
        fragment_area_m2 = math.pi * radius ** 2

    # Retardation exponent
    exponent = -(drag_coefficient * air_density * fragment_area_m2 * distance_m
                 / (2 * fragment_mass_kg))

    return V0_m_s * math.exp(exponent)


def fragment_kinetic_energy(mass_kg: float, velocity_m_s: float) -> float:
    """
    Compute kinetic energy of a fragment:
        KE = 0.5 * m * v²

    Returns:
        KE in Joules
    """
    if mass_kg <= 0 or velocity_m_s < 0:
        raise ValueError("Mass must be > 0 and velocity must be ≥ 0.")
    return 0.5 * mass_kg * velocity_m_s ** 2


def run_all_calculations(explosive_type: str,
                          charge_weight_kg: float,
                          casing_weight_kg: float,
                          casing_thickness_m: float,
                          casing_diameter_m: float,
                          distance_m: float) -> dict:
    """
    Run the full suite of fragment calculations and return results as a dict.

    Parameters
    ----------
    explosive_type      : one of "TNT", "RDX", "HMX", "C4"
    charge_weight_kg    : explosive charge mass [kg]
    casing_weight_kg    : metal casing mass [kg]
    casing_thickness_m  : wall thickness of casing [m]
    casing_diameter_m   : outer diameter of casing [m]
    distance_m          : standoff distance [m]

    Returns
    -------
    dict with keys:
        initial_velocity_m_s, m_avg_kg, m_avg_g,
        m_largest_kg, m_largest_g,
        velocity_at_distance_m_s, kinetic_energy_J,
        n_total, mass_bins, cumulative_counts
    """
    # 1. Initial fragment velocity (Gurney)
    V0 = gurney_velocity(explosive_type, charge_weight_kg, casing_weight_kg)

    # 2. Fragment mass distribution (Mott)
    m_avg, m_largest, mass_bins, cum_counts = mott_fragment_distribution(
        casing_weight_kg, casing_thickness_m, casing_diameter_m, charge_weight_kg
    )

    # 3. Total fragment count (estimated)
    n_total = int(casing_weight_kg / m_avg) if m_avg > 0 else 1

    # 4. Velocity at distance (using average fragment mass)
    V_dist = fragment_velocity_at_distance(V0, distance_m, m_avg)

    # 5. Kinetic energy of average fragment at distance
    KE = fragment_kinetic_energy(m_avg, V_dist)

    return {
        "initial_velocity_m_s":       round(V0, 2),
        "m_avg_kg":                    m_avg,
        "m_avg_g":                     round(m_avg * 1000, 4),
        "m_largest_kg":                m_largest,
        "m_largest_g":                 round(m_largest * 1000, 4),
        "velocity_at_distance_m_s":   round(V_dist, 2),
        "kinetic_energy_J":            round(KE, 4),
        "n_total":                     n_total,
        "mass_bins":                   mass_bins,
        "cumulative_counts":           cum_counts,
    }
