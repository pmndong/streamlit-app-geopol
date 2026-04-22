"""
Moteur de scoring : transforme les indicateurs bruts en scores 0-100.

Scores produits :
  energy_score    — basé sur Brent, variation 7j, VIX
  military_score  — basé sur incidents UCDP (zone Golfe/Iran)
  political_score — proxy basé sur sanctions OFAC récentes + intensité diplomatique
  global_score    — agrégation pondérée des 3 scores
"""
import numpy as np
import pandas as pd
from datetime import timedelta


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #
def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(np.clip(x, lo, hi))


def _normalize(value: float, ref: float, max_val: float) -> float:
    """Normalise linéairement : ref → 0, max_val → 100. Symétrique autour de ref."""
    if max_val == ref:
        return 0.0
    score = (value - ref) / (max_val - ref) * 100
    return _clamp(score)


# ------------------------------------------------------------------ #
#  Score énergétique (date précise)                                    #
# ------------------------------------------------------------------ #
def compute_energy_score(brent: float, brent_7d_chg: float,
                          vix: float, cfg: dict) -> float:
    sc = cfg["scoring"]
    s_brent  = _normalize(brent,          sc["brent_ref"], sc["brent_max"])
    s_change = _normalize(abs(brent_7d_chg), sc["brent_7d_ref"], sc["brent_7d_max"])
    s_vix    = _normalize(vix,            sc["vix_ref"],   sc["vix_max"])
    # Pondérations internes : niveau prix 50%, volatilité 7j 30%, VIX 20%
    return _clamp(0.50 * s_brent + 0.30 * s_change + 0.20 * s_vix)


def energy_score_series(daily: pd.DataFrame, cfg: dict) -> pd.Series:
    """Calcule le score énergie pour chaque ligne du DataFrame journalier."""
    def _row(r):
        brent    = r.get("brent_usd", np.nan)
        chg      = r.get("brent_7d_change_pct", 0.0)
        vix      = r.get("vix_close", cfg["scoring"]["vix_ref"])
        if pd.isna(brent):
            return np.nan
        if pd.isna(chg):
            chg = 0.0
        if pd.isna(vix):
            vix = cfg["scoring"]["vix_ref"]
        return compute_energy_score(brent, chg, vix, cfg)
    return daily.apply(_row, axis=1)


# ------------------------------------------------------------------ #
#  Score militaire (agrégat mensuel UCDP)                              #
# ------------------------------------------------------------------ #
def compute_military_score(nb_incidents: float, total_deaths: float,
                            incidents_trend: float, cfg: dict) -> float:
    sc = cfg["scoring"]
    s_inc    = _normalize(nb_incidents,    sc["incident_ref"], sc["incident_max"])
    s_deaths = _normalize(total_deaths,    sc["deaths_ref"],   sc["deaths_max"])
    s_trend  = _clamp(incidents_trend / sc["incident_max"] * 50 + 50)  # 50 = stable
    # Pondérations : count 40%, décès 40%, tendance 20%
    return _clamp(0.40 * s_inc + 0.40 * s_deaths + 0.20 * s_trend)


def military_score_series(incidents: pd.DataFrame, cfg: dict) -> pd.Series:
    def _row(r):
        return compute_military_score(
            r.get("nb_incidents", 0),
            r.get("total_deaths", 0),
            r.get("incidents_trend", 0),
            cfg,
        )
    return incidents.apply(_row, axis=1)


# ------------------------------------------------------------------ #
#  Score politique (proxy OFAC + intensité conflits politiques)        #
# ------------------------------------------------------------------ #
def compute_political_score_from_sanctions(sanctions: pd.DataFrame,
                                           as_of_date: pd.Timestamp,
                                           cfg: dict) -> float:
    """
    Proxy politique : compte les entités Iran/Yemen/Houthi sanctionnées.
    Le fichier OFAC est statique — on retourne un score fixe basé sur le volume.
    """
    sc = cfg["scoring"]
    n = len(sanctions)
    return _normalize(min(n, sc["sanctions_max"]),
                      sc["sanctions_ref"],
                      sc["sanctions_max"])


def political_score_from_geo(geo: pd.DataFrame,
                              as_of_date: pd.Timestamp,
                              window_days: int = 90) -> float:
    """
    Score politique calculé depuis les événements UCDP :
    - Conflits impliquant Iran, Houthi, IRGC, Hezbollah
    - Type de violence 3 = violence contre civils (= répression / escalade)
    """
    cutoff = as_of_date - timedelta(days=window_days)
    political_actors = ["Iran", "Yemen", "Lebanon", "Bahrain"]
    recent = geo[
        (geo["date_start"] >= cutoff) &
        (geo["date_start"] <= as_of_date) &
        (geo["country"].isin(political_actors))
    ]
    n_events = len(recent)
    total_deaths = recent["best"].sum()
    # Plus il y a d'événements récents dans la zone, plus le score politique est élevé
    s_events = _normalize(n_events, 1, 50)
    s_deaths = _normalize(total_deaths, 5, 300)
    return _clamp(0.60 * s_events + 0.40 * s_deaths)


# ------------------------------------------------------------------ #
#  Score global                                                        #
# ------------------------------------------------------------------ #
def compute_global_score(military: float, political: float,
                          energy: float, cfg: dict) -> float:
    w = cfg["scoring"]
    return _clamp(
        w["weight_military"]  * military +
        w["weight_political"] * political +
        w["weight_energy"]    * energy
    )


# ------------------------------------------------------------------ #
#  Point de score "aujourd'hui" (snapshot)                             #
# ------------------------------------------------------------------ #
def compute_current_scores(daily: pd.DataFrame, incidents: pd.DataFrame,
                            geo: pd.DataFrame, sanctions: pd.DataFrame,
                            cfg: dict, as_of: pd.Timestamp = None) -> dict:
    if as_of is None:
        as_of = daily["date"].max()

    # Energy
    row = daily[daily["date"] <= as_of].iloc[-1]
    energy  = compute_energy_score(
        row["brent_usd"], row.get("brent_7d_change_pct", 0),
        row.get("vix_close", cfg["scoring"]["vix_ref"]), cfg
    )

    # Military (dernier mois disponible)
    last_inc = incidents.iloc[-1] if len(incidents) > 0 else {}
    military = compute_military_score(
        last_inc.get("nb_incidents", 0),
        last_inc.get("total_deaths", 0),
        last_inc.get("incidents_trend", 0),
        cfg,
    )

    # Political
    political = political_score_from_geo(geo, as_of, window_days=90)

    # Global
    global_score = compute_global_score(military, political, energy, cfg)

    return {
        "energy_score":   round(energy, 1),
        "military_score": round(military, 1),
        "political_score": round(political, 1),
        "global_score":   round(global_score, 1),
        "brent_usd":      round(row["brent_usd"], 2),
        "brent_7d_chg":   round(row.get("brent_7d_change_pct", 0) * 100, 2),
        "vix":            round(row.get("vix_close", cfg["scoring"]["vix_ref"]), 2),
        "as_of":          as_of,
    }
