"""
Module d'exposition entreprise.

Score entreprise = 0.5 × oil_dependency + 0.3 × hormuz_exposure + 0.2 × sector_sensitivity

Puis croisement avec le risque conflit (global_score) pour produire :
  - risk_adjusted : exposition nette sous scénario courant
  - risk_category : Faible / Modéré / Élevé / Critique
"""
import numpy as np
import pandas as pd


RISK_LABELS = {
    "Critique": {"color": "#E74C3C", "icon": "🔴"},
    "Élevé":    {"color": "#E67E22", "icon": "🟠"},
    "Modéré":   {"color": "#F1C40F", "icon": "🟡"},
    "Faible":   {"color": "#2ECC71", "icon": "🟢"},
}

IMPACT_TYPES = {
    "Critique": [
        "Rupture d'approvisionnement directe",
        "Hausse coût matières premières > 30%",
        "Risque de continuité opérationnelle",
        "Pression EBITDA sévère",
    ],
    "Élevé": [
        "Hausse coût approvisionnement 15–30%",
        "Tension sur la supply chain",
        "Pression marges significative",
        "Surcoûts logistiques importants",
    ],
    "Modéré": [
        "Hausse coût énergie 5–15%",
        "Impact modéré sur les marges",
        "Surcharges carburant potentielles",
    ],
    "Faible": [
        "Impact marginal sur les coûts",
        "Exposition indirecte via inflation",
    ],
}


def compute_company_scores(companies: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Recalcule le score entreprise depuis les composantes brutes."""
    df = companies.copy()
    w = cfg["company_risk"]
    df["company_risk_score"] = (
        w["weight_oil_dependency"]     * df["oil_dependency_score"] +
        w["weight_hormuz_exposure"]    * df["hormuz_exposure_score"] +
        w["weight_sector_sensitivity"] * df["sector_sensitivity_score"]
    ).round(3)

    t = cfg["company_risk"]["thresholds"]
    def _label(s):
        if s >= t["critique"]: return "Critique"
        elif s >= t["eleve"]:  return "Élevé"
        elif s >= t["modere"]: return "Modéré"
        else:                  return "Faible"

    df["risk_level"] = df["company_risk_score"].apply(_label)
    return df


def adjust_for_scenario(companies: pd.DataFrame,
                         global_score: float,
                         dominant_scenario: str) -> pd.DataFrame:
    """
    Ajuste le risque entreprise selon le scénario courant.
    Scénario C → amplifie l'exposition ; Scénario A → réduit.
    """
    df = companies.copy()
    multipliers = {"A": 0.70, "B": 1.00, "C": 1.35}
    mult = multipliers.get(dominant_scenario, 1.0)
    # Modulation par score global également
    tension_factor = 0.5 + global_score / 200  # entre 0.5 (score=0) et 1.0 (score=100)
    df["risk_adjusted"] = (df["company_risk_score"] * mult * tension_factor).clip(0, 1).round(3)

    t_adj = {"critique": 0.75, "eleve": 0.55, "modere": 0.35}
    def _label(s):
        if s >= t_adj["critique"]: return "Critique"
        elif s >= t_adj["eleve"]:  return "Élevé"
        elif s >= t_adj["modere"]: return "Modéré"
        else:                      return "Faible"

    df["risk_level_adjusted"] = df["risk_adjusted"].apply(_label)
    return df


def get_top_exposed(companies: pd.DataFrame, n: int = 10,
                    score_col: str = "risk_adjusted") -> pd.DataFrame:
    return companies.nlargest(n, score_col).reset_index(drop=True)


def get_sector_summary(companies: pd.DataFrame,
                        score_col: str = "risk_adjusted") -> pd.DataFrame:
    """Résumé par secteur : score moyen, nb entreprises critiques."""
    agg = companies.groupby("sector").agg(
        nb_companies=("company", "count"),
        avg_risk=(score_col, "mean"),
        max_risk=(score_col, "max"),
        nb_critique=("risk_level_adjusted",
                     lambda x: (x == "Critique").sum()),
        nb_eleve=("risk_level_adjusted",
                  lambda x: (x == "Élevé").sum()),
    ).reset_index()
    agg["avg_risk"] = agg["avg_risk"].round(3)
    agg["max_risk"] = agg["max_risk"].round(3)
    return agg.sort_values("avg_risk", ascending=False).reset_index(drop=True)


def get_impact_description(risk_level: str) -> list:
    return IMPACT_TYPES.get(risk_level, [])
