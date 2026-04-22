"""
APPLICATION STREAMLIT — RISQUE GÉOPOLITIQUE ORMUZ
Point d'entrée principal (app.py)
"""
import streamlit as st
import sys
from pathlib import Path

# ---- Ajout du dossier racine au path ----
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_all, load_config
from src.feature_engineering import enrich_oil, enrich_vix, incidents_by_month, merge_daily_features
from src.scoring import compute_current_scores
from src.scenario_engine import compute_scenario_probabilities, get_scenario_narrative
from src.company_risk import compute_company_scores, adjust_for_scenario
from src.utils import score_to_color, score_to_label

# ---- Config page ----
st.set_page_config(
    page_title="Risque Ormuz",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Chargement données (cached) ----
@st.cache_data(ttl=3600)
def load_data():
    data = load_all()
    data["oil"]  = enrich_oil(data["oil"])
    data["vix"]  = enrich_vix(data["vix"])
    data["daily"] = merge_daily_features(data["oil"], data["vix"])
    data["incidents"] = incidents_by_month(data["geo"])
    data["companies"] = compute_company_scores(data["companies"], data["cfg"])
    return data


# ---- Stockage en session ----
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
cfg  = data["cfg"]

# ---- Scores courants ----
scores = compute_current_scores(
    data["daily"], data["incidents"],
    data["geo"], data["sanctions"], cfg
)
probs, dominant = compute_scenario_probabilities(
    scores["global_score"], scores["energy_score"],
    scores["military_score"], scores["political_score"],
)
companies = adjust_for_scenario(data["companies"], scores["global_score"], dominant)

# Injection dans la session pour les pages
st.session_state.scores    = scores
st.session_state.probs     = probs
st.session_state.dominant  = dominant
st.session_state.companies = companies
st.session_state.cfg       = cfg
st.session_state.data      = data

# ---- Sidebar ----
st.sidebar.title("🛢️ Risque Ormuz")
st.sidebar.caption(f"Données au : **{scores['as_of'].strftime('%d %b %Y')}**")

st.sidebar.markdown("---")
color = score_to_color(scores["global_score"])
label = score_to_label(scores["global_score"])
st.sidebar.markdown(
    f"**Score global :** "
    f"<span style='color:{color};font-size:1.3em;font-weight:bold'>"
    f"{scores['global_score']:.0f}/100 — {label}</span>",
    unsafe_allow_html=True,
)

scen_colors = {"A": "#2ECC71", "B": "#F39C12", "C": "#E74C3C"}
scen_names  = {
    "A": "Désescalade rapide",
    "B": "Tension contrôlée",
    "C": "Escalade régionale",
}
sc_col = scen_colors[dominant]
st.sidebar.markdown(
    f"**Scénario dominant :** "
    f"<span style='color:{sc_col};font-weight:bold'>{dominant} — {scen_names[dominant]}</span>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")
st.sidebar.page_link("app.py",                       label="🏠 Accueil")
st.sidebar.page_link("pages/1_Executive_Summary.py", label="📊 Vue Exécutive")
st.sidebar.page_link("pages/2_Indicators.py",        label="📈 Indicateurs")
st.sidebar.page_link("pages/3_Scoring.py",           label="⚙️ Scores & Moteur")
st.sidebar.page_link("pages/4_Scenarios.py",         label="🎯 Scénarios")
st.sidebar.page_link("pages/5_Company_Risk.py",      label="🏭 Impact Entreprises")

# ---- Page d'accueil ----
st.title("🛢️ Analyseur de Risque Géopolitique — Détroit d'Ormuz")
st.markdown(
    """
    Cette application centralise les **indicateurs géopolitiques, énergétiques et logistiques**
    liés au détroit d'Ormuz — axe de transit de ~20% du pétrole mondial.

    Elle calcule des **scores de tension**, les convertit en **scénarios probabilisés**,
    et mesure l'**impact potentiel sur les entreprises exposées**.
    """
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Score Global", f"{scores['global_score']:.0f}/100",
              delta=None)
with col2:
    st.metric("Brent ($/b)", f"{scores['brent_usd']:.1f}",
              delta=f"{scores['brent_7d_chg']:+.1f}% (7j)")
with col3:
    st.metric("VIX", f"{scores['vix']:.1f}")
with col4:
    st.metric("Scénario dominant",
              f"{dominant} — {scen_names[dominant]}")

st.markdown("---")
st.subheader("Utilisation de l'application")
cols = st.columns(5)
pages = [
    ("📊", "Vue Exécutive",     "Tableau de bord instantané : scénario, durée, risque global."),
    ("📈", "Indicateurs",        "Brent, VIX, incidents UCDP — séries temporelles."),
    ("⚙️", "Scores & Moteur",   "Décomposition des 3 scores et pondérations."),
    ("🎯", "Scénarios",          "Probabilités A/B/C + simulation manuelle."),
    ("🏭", "Impact Entreprises", "Classement des entreprises et secteurs les plus exposés."),
]
for col, (icon, title, desc) in zip(cols, pages):
    with col:
        st.markdown(f"**{icon} {title}**")
        st.caption(desc)

st.markdown("---")
st.caption(
    "Sources : EIA (Brent/WTI), CBOE (VIX), UCDP GED (conflits), OFAC (sanctions). "
    "Ce système est un outil d'aide à la décision — pas un moteur de prédiction exacte."
)
