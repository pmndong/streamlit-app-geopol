"""Utilitaires partagés."""
import pandas as pd
import numpy as np


def score_to_color(score: float) -> str:
    if score >= 65: return "#E74C3C"
    elif score >= 45: return "#F39C12"
    elif score >= 25: return "#F1C40F"
    else: return "#2ECC71"


def score_to_label(score: float) -> str:
    if score >= 65: return "CRITIQUE"
    elif score >= 45: return "ÉLEVÉ"
    elif score >= 25: return "MODÉRÉ"
    else: return "FAIBLE"


def pct_fmt(v: float) -> str:
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


def fmt_score(v: float) -> str:
    return f"{v:.0f} / 100"


def risk_color(level: str) -> str:
    mapping = {
        "Critique": "#E74C3C",
        "Élevé":    "#E67E22",
        "Modéré":   "#F1C40F",
        "Faible":   "#2ECC71",
    }
    return mapping.get(level, "#95A5A6")


def last_n_days(df: pd.DataFrame, date_col: str, n: int) -> pd.DataFrame:
    max_date = df[date_col].max()
    cutoff   = max_date - pd.Timedelta(days=n)
    return df[df[date_col] >= cutoff]
