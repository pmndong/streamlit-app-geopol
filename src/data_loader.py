"""Chargement des données depuis les CSV."""
import os
import yaml
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "parameters.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _abs(cfg_path: str) -> Path:
    return BASE_DIR / cfg_path


def load_oil(cfg: dict) -> pd.DataFrame:
    df = pd.read_csv(_abs(cfg["data"]["path_oil"]), parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def load_vix(cfg: dict) -> pd.DataFrame:
    df = pd.read_csv(_abs(cfg["data"]["path_vix"]), parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def load_geo_events(cfg: dict) -> pd.DataFrame:
    df = pd.read_csv(_abs(cfg["data"]["path_geo"]), parse_dates=["date_start"])
    return df.sort_values("date_start").reset_index(drop=True)


def load_companies(cfg: dict) -> pd.DataFrame:
    return pd.read_csv(_abs(cfg["data"]["path_companies"]))


def load_sanctions(cfg: dict) -> pd.DataFrame:
    return pd.read_csv(
        _abs(cfg["data"]["path_sanctions"]), encoding="utf-8-sig", low_memory=False
    )


def load_all(cfg: dict = None) -> dict:
    if cfg is None:
        cfg = load_config()
    return {
        "oil":       load_oil(cfg),
        "vix":       load_vix(cfg),
        "geo":       load_geo_events(cfg),
        "companies": load_companies(cfg),
        "sanctions": load_sanctions(cfg),
        "cfg":       cfg,
    }
