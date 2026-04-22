"""Page 1 — Vue Exécutive."""
import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import score_to_color, score_to_label, risk_color
from src.scenario_engine import get_scenario_narrative

st.set_page_config(page_title="Vue Exécutive — Ormuz", page_icon="📊", layout="wide")
st.title("📊 Vue Exécutive")

if "scores" not in st.session_state:
    st.warning("Rechargez l'application depuis la page d'accueil.")
    st.stop()

scores   = st.session_state.scores
probs    = st.session_state.probs
dominant = st.session_state.dominant
cfg      = st.session_state.cfg

scen_names  = {"A": "Désescalade rapide", "B": "Tension contrôlée", "C": "Escalade régionale"}
scen_colors = {"A": "#2ECC71", "B": "#F39C12", "C": "#E74C3C"}
scen_durations = {
    "A": "1 – 3 mois",
    "B": "3 – 12 mois",
    "C": "12 mois et plus",
}

# ---- Bandeau alerte ----
g = scores["global_score"]
if g >= 65:
    st.error(f"⚠️ ALERTE — Niveau de tension CRITIQUE ({g:.0f}/100). Risque d'escalade régionale.")
elif g >= 45:
    st.warning(f"⚡ ATTENTION — Niveau de tension ÉLEVÉ ({g:.0f}/100). Surveiller l'évolution.")
else:
    st.success(f"✅ Niveau de tension MODÉRÉ ({g:.0f}/100). Situation sous contrôle.")

st.markdown("---")

# ---- KPI cards ----
c1, c2, c3, c4 = st.columns(4)
with c1:
    color = score_to_color(g)
    label = score_to_label(g)
    st.markdown(
        f"""
        <div style='background:{color}22;border-left:4px solid {color};
                    padding:16px;border-radius:6px;'>
        <div style='font-size:0.85em;color:#666'>Score de tension global</div>
        <div style='font-size:2.2em;font-weight:bold;color:{color}'>{g:.0f}</div>
        <div style='font-size:0.9em;color:{color}'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

with c2:
    sc = scen_colors[dominant]
    sn = scen_names[dominant]
    sd = scen_durations[dominant]
    st.markdown(
        f"""
        <div style='background:{sc}22;border-left:4px solid {sc};
                    padding:16px;border-radius:6px;'>
        <div style='font-size:0.85em;color:#666'>Scénario dominant</div>
        <div style='font-size:1.5em;font-weight:bold;color:{sc}'>Scénario {dominant}</div>
        <div style='font-size:0.9em'>{sn}</div>
        <div style='font-size:0.8em;color:#888'>Durée estimée : {sd}</div>
        </div>
        """, unsafe_allow_html=True)

with c3:
    st.markdown(
        f"""
        <div style='background:#2980B922;border-left:4px solid #2980B9;
                    padding:16px;border-radius:6px;'>
        <div style='font-size:0.85em;color:#666'>Brent (spot)</div>
        <div style='font-size:2.2em;font-weight:bold;color:#2980B9'>${scores['brent_usd']:.1f}</div>
        <div style='font-size:0.9em;color:{"#E74C3C" if scores["brent_7d_chg"]>0 else "#2ECC71"}'>
            {scores["brent_7d_chg"]:+.1f}% sur 7 jours</div>
        </div>
        """, unsafe_allow_html=True)

with c4:
    vix_col = "#E74C3C" if scores["vix"] > 30 else ("#F39C12" if scores["vix"] > 20 else "#2ECC71")
    st.markdown(
        f"""
        <div style='background:{vix_col}22;border-left:4px solid {vix_col};
                    padding:16px;border-radius:6px;'>
        <div style='font-size:0.85em;color:#666'>VIX (volatilité globale)</div>
        <div style='font-size:2.2em;font-weight:bold;color:{vix_col}'>{scores['vix']:.1f}</div>
        <div style='font-size:0.9em'>{"Élevé" if scores["vix"]>30 else ("Modéré" if scores["vix"]>20 else "Bas")}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ---- Jauge tension ----
col_gauge, col_prob = st.columns([1, 1])

with col_gauge:
    st.subheader("Jauge de tension")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=g,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Score Global / 100"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": score_to_color(g)},
            "steps": [
                {"range": [0, 35],  "color": "rgba(46,204,113,0.18)"},
                {"range": [35, 65], "color": "rgba(243,156,18,0.18)"},
                {"range": [65, 100],"color": "rgba(231,76,60,0.18)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.75,
                "value": g,
            },
        },
    ))
    fig.update_layout(height=280, margin=dict(t=30, b=0, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

with col_prob:
    st.subheader("Probabilités scénarios")
    fig2 = go.Figure(go.Bar(
        x=["A — Désescalade", "B — Tension contrôlée", "C — Escalade"],
        y=[probs["A"] * 100, probs["B"] * 100, probs["C"] * 100],
        marker_color=[scen_colors["A"], scen_colors["B"], scen_colors["C"]],
        text=[f"{probs['A']*100:.0f}%", f"{probs['B']*100:.0f}%", f"{probs['C']*100:.0f}%"],
        textposition="outside",
    ))
    fig2.update_layout(
        yaxis=dict(title="Probabilité (%)", range=[0, 110]),
        height=280,
        margin=dict(t=30, b=0, l=20, r=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ---- Top 3 facteurs explicatifs ----
st.subheader("Facteurs explicatifs principaux")

factors = sorted([
    ("Score Énergétique",  scores["energy_score"],  "Brent, volatilité, VIX"),
    ("Score Militaire",    scores["military_score"], "Incidents UCDP — Golfe Persique"),
    ("Score Politique",    scores["political_score"],"Événements politiques — Liban, Iran, Yémen"),
], key=lambda x: x[1], reverse=True)

for rank, (name, score, source) in enumerate(factors, 1):
    col_r, col_s, col_b = st.columns([2, 5, 1])
    with col_r:
        st.markdown(f"**#{rank} — {name}**")
        st.caption(source)
    with col_s:
        bar_pct = int(score)
        col = score_to_color(score)
        st.markdown(
            f"<div style='background:#eee;border-radius:4px;height:18px;margin-top:8px'>"
            f"<div style='background:{col};width:{bar_pct}%;height:100%;border-radius:4px'></div>"
            f"</div>",
            unsafe_allow_html=True)
    with col_b:
        st.markdown(f"**{score:.0f}/100**")

st.markdown("---")

# ---- Narratif scénario ----
st.subheader("Analyse du scénario")
narrative = get_scenario_narrative(dominant, scores)
sc = scen_colors[dominant]
st.markdown(
    f"<div style='background:{sc}11;border-left:4px solid {sc};"
    f"padding:14px;border-radius:6px;font-size:0.95em'>{narrative}</div>",
    unsafe_allow_html=True)
