"""
Moteur de scénarios : convertit les scores en probabilités et scénario dominant.

Logique :
  score < 35  → scénario A dominant
  35–65       → scénario B dominant
  > 65        → scénario C dominant

Les probabilités sont redistribuées avec modulation par sous-scores.
"""
import numpy as np
from typing import Tuple


def _softmax_like(scores: list[float], temperature: float = 15.0) -> list[float]:
    """Redistribution douce : l'écart de score influence la probabilité."""
    arr = np.array(scores, dtype=float)
    arr = arr / temperature
    exp = np.exp(arr - arr.max())
    return (exp / exp.sum()).tolist()


def compute_scenario_probabilities(
    global_score: float,
    energy_score: float,
    military_score: float,
    political_score: float,
) -> Tuple[dict, str]:
    """
    Retourne :
      - dict {A, B, C} avec probabilités (somme = 1.0)
      - scénario dominant (str)
    """
    # Scores de base pour chaque scénario selon le score global
    # A : favorisé si score bas, C : favorisé si score haut
    base_a = max(0, 35 - global_score) * 2       # max 70 si score=0
    base_b = 100 - abs(global_score - 50) * 1.5  # max 100 si score=50
    base_c = max(0, global_score - 65) * 3        # max 105 si score=100

    # Modulations par sous-scores
    # Si énergie explose → augmente C
    if energy_score > 75:
        base_c += (energy_score - 75) * 0.8
        base_a -= 10
    # Si militaire très élevé → augmente C
    if military_score > 70:
        base_c += (military_score - 70) * 0.5
    # Si politique baisse → remonte A
    if political_score < 25:
        base_a += (25 - political_score) * 0.6
        base_b -= 5

    # Normalisation
    total = base_a + base_b + base_c
    if total <= 0:
        total = 1.0
    probs = {
        "A": round(max(0, base_a / total), 3),
        "B": round(max(0, base_b / total), 3),
        "C": round(max(0, base_c / total), 3),
    }

    # Renormalisation finale à 1.0
    s = sum(probs.values())
    if s > 0:
        probs = {k: round(v / s, 3) for k, v in probs.items()}

    dominant = max(probs, key=probs.get)
    return probs, dominant


def get_scenario_info(scenario: str, cfg: dict) -> dict:
    return cfg["scenarios"].get(scenario, {})


def get_scenario_narrative(dominant: str, scores: dict) -> str:
    """Génère une explication textuelle simple du scénario."""
    g = scores["global_score"]
    e = scores["energy_score"]
    m = scores["military_score"]
    p = scores["political_score"]
    brent = scores["brent_usd"]
    chg   = scores["brent_7d_chg"]

    drivers = []
    if e > 60:
        drivers.append(f"prix du Brent élevé ({brent:.0f} $/b, +{chg:.1f}% sur 7j)")
    if m > 60:
        drivers.append("incidents militaires récurrents dans la zone du Golfe")
    if p > 50:
        drivers.append("tension politique élevée (Iran, Yémen, Liban)")
    if not drivers:
        drivers.append("indicateurs globalement modérés")

    scenario_texts = {
        "A": (
            f"Le score global de {g:.0f}/100 reflète une tension en recul. "
            f"Les principaux signaux convergent vers une désescalade : "
            + " ; ".join(drivers) + "."
        ),
        "B": (
            f"Le score global de {g:.0f}/100 traduit une tension soutenue mais contenue. "
            f"Facteurs dominants : " + " ; ".join(drivers) + ". "
            "Le statu quo conflictuel devrait se maintenir sans rupture majeure."
        ),
        "C": (
            f"Le score global de {g:.0f}/100 signale un risque d'escalade régionale. "
            f"Facteurs déclenchants : " + " ; ".join(drivers) + ". "
            "Une perturbation durable du transit pétrolier via Ormuz est envisageable."
        ),
    }
    return scenario_texts.get(dominant, "")
