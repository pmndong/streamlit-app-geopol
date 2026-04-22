"""Page 4 — Scénarios & Simulation."""
import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scoring import compute_energy_score, compute_military_score, compute_political_score_from_sanctions, compute_global_score
from src.scenario_engine import compute_scenario_probabilities, get_scenario_narrative, get_scenario_info
from src.company_risk import adjust_for_scenario
from src.utils import score_to_color

st.set_page_config(page_title="Scénarios — Ormuz", page_icon="🎯", layout="wide")
st.title("🎯 Scénarios & Simulation")

if "scores" not in st.session_state:
    st.warning("Rechargez l'application depuis la page d'accueil.")
    st.stop()

scores    = st.session_state.scores
probs     = st.session_state.probs
dominant  = st.session_state.dominant
cfg       = st.session_state.cfg
data      = st.session_state.data

scen_colors = {"A": "#2ECC71", "B": "#F39C12", "C": "#E74C3C"}
scen_names  = {"A": "Désescalade rapide",
               "B": "Conflit prolongé sous tension contrôlée",
               "C": "Escalade régionale durable"}
scen_durations = {"A": "1 – 3 mois", "B": "3 – 12 mois", "C": "12 mois et plus"}

# ---- Section résultats courants ----
st.subheader("Situation courante")

c1, c2, c3 = st.columns(3)
for col, sc in zip([c1, c2, c3], ["A", "B", "C"]):
    pct = probs[sc] * 100
    color = scen_colors[sc]
    is_dom = sc == dominant
    border = f"3px solid {color}" if is_dom else f"1px solid {color}44"
    with col:
        st.markdown(
            f"""<div style='border:{border};border-radius:8px;padding:16px;
                background:{color}{"22" if is_dom else "0A"}'>
            <div style='font-size:.85em;color:#666'>Scénario {sc} {"★ DOMINANT" if is_dom else ""}</div>
            <div style='font-size:1.4em;font-weight:bold;color:{color}'>{scen_names[sc]}</div>
            <div style='font-size:2.5em;font-weight:bold;color:{color}'>{pct:.0f}%</div>
            <div style='font-size:.8em;color:#888'>Durée : {scen_durations[sc]}</div>
            </div>""",
            unsafe_allow_html=True)

st.markdown("")

# Graphique probabilités
fig = go.Figure()
fig.add_trace(go.Bar(
    x=["A — Désescalade", "B — Tension contrôlée", "C — Escalade"],
    y=[probs["A"]*100, probs["B"]*100, probs["C"]*100],
    marker_color=[scen_colors["A"], scen_colors["B"], scen_colors["C"]],
    text=[f"{probs['A']*100:.0f}%", f"{probs['B']*100:.0f}%", f"{probs['C']*100:.0f}%"],
    textposition="outside", textfont=dict(size=16),
    width=0.5,
))
fig.update_layout(
    yaxis=dict(title="Probabilité (%)", range=[0, 115]),
    height=320, margin=dict(t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# Narratif
sc_col = scen_colors[dominant]
narrative = get_scenario_narrative(dominant, scores)
st.markdown(
    f"<div style='background:{sc_col}11;border-left:5px solid {sc_col};"
    f"padding:14px;border-radius:6px;font-size:.95em'>{narrative}</div>",
    unsafe_allow_html=True)

st.markdown("---")

# ================================================================
# SIMULATION MANUELLE
# ================================================================
st.subheader("🔧 Stress-test Manuel")
st.markdown(
    "Ajustez les sliders pour simuler des chocs de marché ou d'intensité "
    "et observer l'impact sur les probabilités de scénario."
)

col_sl, col_res = st.columns([1, 1])

with col_sl:
    brent_shock = st.slider(
        "Hausse Brent ($/b)", min_value=-40, max_value=80, value=0, step=5,
        help="Variation additionnelle du prix du Brent par rapport au niveau actuel.")
    incidents_mult = st.slider(
        "Multiplicateur incidents militaires", min_value=0.2, max_value=5.0, value=1.0, step=0.2,
        help="1.0 = situation actuelle. 2.0 = incidents × 2.")
    ormuz_disruption = st.slider(
        "Perturbation Ormuz (%)", min_value=0, max_value=100, value=0, step=10,
        help="Pourcentage de fermeture estimé du détroit.")
    political_boost = st.slider(
        "Tensions politiques (bonus score)", min_value=-20, max_value=40, value=0, step=5,
        help="Bonus/malus sur le score politique.")

# Calcul scores simulés
brent_sim   = scores["brent_usd"] + brent_shock
chg_sim     = scores["brent_7d_chg"] / 100 + (brent_shock / scores["brent_usd"] if scores["brent_usd"] > 0 else 0)
vix_sim     = scores["vix"] + ormuz_disruption * 0.3  # perturbation Ormuz → hausse VIX

energy_sim  = compute_energy_score(brent_sim, chg_sim, vix_sim, cfg)

last_inc    = data["incidents"].iloc[-1]
inc_sim     = last_inc.get("nb_incidents", 0) * incidents_mult
deaths_sim  = last_inc.get("total_deaths", 0) * incidents_mult
trend_sim   = last_inc.get("incidents_trend", 0) * incidents_mult
military_sim = compute_military_score(inc_sim, deaths_sim, trend_sim, cfg)
military_sim = min(100, military_sim + ormuz_disruption * 0.2)

political_sim = min(100, scores["political_score"] + political_boost)

global_sim  = compute_global_score(military_sim, political_sim, energy_sim, cfg)
probs_sim, dominant_sim = compute_scenario_probabilities(
    global_sim, energy_sim, military_sim, political_sim)

with col_res:
    st.markdown("**Résultats de la simulation**")

    def delta_str(new, base):
        d = new - base
        sign = "+" if d >= 0 else ""
        return f"{new:.0f} ({sign}{d:.0f})"

    st.markdown(f"- Score Énergétique : **{energy_sim:.0f}** *(base : {scores['energy_score']:.0f})*")
    st.markdown(f"- Score Militaire : **{military_sim:.0f}** *(base : {scores['military_score']:.0f})*")
    st.markdown(f"- Score Politique : **{political_sim:.0f}** *(base : {scores['political_score']:.0f})*")
    st.markdown(f"- **Score Global : {global_sim:.0f}** *(base : {scores['global_score']:.0f})*")
    st.markdown("---")

    sc2 = scen_colors[dominant_sim]
    st.markdown(
        f"<div style='background:{sc2}22;border-left:4px solid {sc2};"
        f"padding:12px;border-radius:6px'>"
        f"<b>Scénario dominant :</b> "
        f"<span style='color:{sc2};font-size:1.1em'>{dominant_sim} — {scen_names[dominant_sim]}</span><br>"
        f"A : <b>{probs_sim['A']*100:.0f}%</b> | "
        f"B : <b>{probs_sim['B']*100:.0f}%</b> | "
        f"C : <b>{probs_sim['C']*100:.0f}%</b>"
        f"</div>", unsafe_allow_html=True)

    # Comparaison visuelle
    fig2 = go.Figure()
    cats = ["A", "B", "C"]
    fig2.add_trace(go.Bar(
        name="Situation actuelle",
        x=cats, y=[probs[c]*100 for c in cats],
        marker_color=[scen_colors[c] for c in cats],
        opacity=0.4))
    fig2.add_trace(go.Bar(
        name="Simulation",
        x=cats, y=[probs_sim[c]*100 for c in cats],
        marker_color=[scen_colors[c] for c in cats],
        marker_line=dict(width=2, color="black")))
    fig2.update_layout(
        barmode="group", height=260,
        yaxis=dict(range=[0, 110], title="%"),
        legend=dict(orientation="h", y=1.05),
        margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ---- Fiches scénarios ----
st.subheader("Fiches scénarios de référence")
tabs = st.tabs(["Scénario A — Désescalade", "Scénario B — Tension contrôlée",
                "Scénario C — Escalade régionale"])
fiche_data = {
    "A": {
        "conditions": [
            "Score global < 35",
            "Incidents militaires stables ou en baisse",
            "Ton diplomatique moins agressif",
            "Trafic Ormuz stable",
            "Prix Brent ≤ 80 $/b",
        ],
        "impacts": [
            "Prix pétrole revient vers 70–80 $/b",
            "Primes assurance maritime se normalisent",
            "Supply chain stabilisée",
            "Pression marges entreprises exposées en baisse",
        ],
    },
    "B": {
        "conditions": [
            "Score global entre 35 et 65",
            "Incidents récurrents mais sans fermeture durable",
            "Prix pétrole élevé (80–120 $/b) mais sans rupture",
            "Menaces fréquentes, escalade contenue",
        ],
        "impacts": [
            "Surcoûts approvisionnement +15–30%",
            "Marges comprimées pour tankers et raffineurs",
            "Primes carburant aviation",
            "Supply chain sous tension mais non rompue",
        ],
    },
    "C": {
        "conditions": [
            "Score global > 65",
            "Incidents croissants, extension régionale",
            "Forte tension politique (Iran, Houthi, Hezbollah)",
            "Perturbation logistique ou énergétique significative",
            "Prix Brent > 120 $/b",
        ],
        "impacts": [
            "Rupture d'approvisionnement possible",
            "Hausse Brent > 130–160 $/b",
            "Fermeture partielle ou totale du détroit",
            "Impact EBITDA sévère pour entreprises critiques",
            "Risque de continuité opérationnelle",
        ],
    },
}
for tab, sc in zip(tabs, ["A", "B", "C"]):
    with tab:
        fd = fiche_data[sc]
        color = scen_colors[sc]
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Conditions de déclenchement**")
            for c in fd["conditions"]:
                st.markdown(f"- {c}")
        with col_b:
            st.markdown(f"**Impacts business typiques**")
            for i in fd["impacts"]:
                st.markdown(f"- {i}")
