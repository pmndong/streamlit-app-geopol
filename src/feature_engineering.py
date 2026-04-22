"""Calcul des features temporelles : variations, moyennes mobiles, scores bruts."""
import numpy as np
import pandas as pd


def enrich_oil(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute variations et moyennes mobiles sur le prix du Brent."""
    df = df.copy().sort_values("date").reset_index(drop=True)
    df["brent_7d_change_pct"]  = df["brent_usd"].pct_change(7,  fill_method=None)
    df["brent_30d_change_pct"] = df["brent_usd"].pct_change(30, fill_method=None)
    df["brent_ma20"]           = df["brent_usd"].rolling(20).mean()
    df["brent_ma60"]           = df["brent_usd"].rolling(60).mean()
    df["brent_above_ma60"]     = (df["brent_usd"] > df["brent_ma60"]).astype(float)
    return df


def enrich_vix(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date").reset_index(drop=True)
    df["vix_7d_change"] = df["vix_close"].pct_change(7)
    df["vix_ma20"]      = df["vix_close"].rolling(20).mean()
    return df


def incidents_by_month(geo: pd.DataFrame) -> pd.DataFrame:
    """Agrège les incidents UCDP par mois pour la zone Golfe/Iran."""
    gulf = ["Iran", "Iraq", "Yemen", "Saudi Arabia", "United Arab Emirates",
            "Oman", "Bahrain", "Kuwait", "Qatar"]
    g = geo[geo["country"].isin(gulf)].copy()
    g["month"] = g["date_start"].dt.to_period("M")
    agg = g.groupby("month").agg(
        nb_incidents=("id", "count"),
        total_deaths=("best", "sum"),
        deaths_civilians=("deaths_civilians", "sum"),
    ).reset_index()
    agg["month_dt"] = agg["month"].dt.to_timestamp()
    agg["incidents_3m_avg"] = agg["nb_incidents"].rolling(3, min_periods=1).mean()
    agg["incidents_trend"]  = agg["nb_incidents"].diff(3).fillna(0)
    return agg.sort_values("month_dt").reset_index(drop=True)


def merge_daily_features(oil: pd.DataFrame, vix: pd.DataFrame) -> pd.DataFrame:
    """Fusionne oil + vix sur une série quotidienne commune."""
    merged = pd.merge(oil, vix, on="date", how="outer").sort_values("date")
    merged = merged.ffill().reset_index(drop=True)
    return merged
