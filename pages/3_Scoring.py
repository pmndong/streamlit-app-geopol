"""Page 3 — Scores & Moteur d'analyse."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scoring import energy_score_series, military_score_series, compute_global_score
from src.utils import score_to_color, score_to_label

st.set_page_config(page_title="Scores — Ormuz", page_icon="⚙️", layout="wide")
st.title("⚙️ Scores & Moteur d'Analyse")

if "scores" not in st.session_state:
    st.warning("Rechargez l'application depuis la page d'accueil.")
    st.stop()

scores    = st.session_state.scores
data      = st.session_state.data
cfg       = st.session_state.cfg

# ---- KPIs scores courants ----
st.subheader("Scores au " + scores["as_of"].strftime("%d %b %Y"))

cols = st.columns(4)
labels = {
    "energy_score":   ("Score Énergétique",  "Brent + VIX + vol. 7j"),
    "military_score": ("Score Militaire",    "Incidents UCDP Golfe"),
    "political_score":("Score Politique",    "Événements Iran/Yémen/Liban"),
    "global_score":   ("Score Global",       "Agrégat pondéré"),
}
for col, (key, (name, src)) in zip(cols, labels.items()):
    v = scores[key]
    c = score_to_color(v)
    with col:
        st.markdown(
            f"<div style='border-left:4px solid {c};padding:12px;"
            f"background:{c}15;border-radius:6px'>"
            f"<div style='font-size:.8em;color:#666'>{name}</div>"
            f"<div style='font-size:2em;font-weight:bold;color:{c}'>{v:.0f}</div>"
            f"<div style='font-size:.75em;color:#888'>{src}</div>"
            f"</div>", unsafe_allow_html=True)

st.markdown("---")

# ---- Waterfall contribution ----
st.subheader("Contribution de chaque composante au score global")
w  = cfg["scoring"]
contributions = {
    "Score Militaire"  : w["weight_military"]  * scores["military_score"],
    "Score Politique"  : w["weight_political"] * scores["political_score"],
    "Score Énergétique": w["weight_energy"]    * scores["energy_score"],
}
labels_wf  = list(contributions.keys()) + ["Score Global"]
values_wf  = list(contributions.values())
total      = sum(values_wf)
measure    = ["relative"] * len(values_wf) + ["total"]
values_wf += [total]
colors_wf  = [score_to_color(v / (w["weight_military"] if i==0
                                   else w["weight_political"] if i==1
                                   else w["weight_energy"]) )
              for i, v in enumerate(values_wf[:-1])] + [score_to_color(total)]

fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=measure,
    x=labels_wf,
    y=values_wf,
    connector={"line": {"color": "#ccc"}},
    increasing={"marker": {"color": "#E74C3C"}},
    totals={"marker": {"color": score_to_color(total)}},
    text=[f"{v:.1f}" for v in values_wf],
    textposition="outside",
))
fig_wf.update_layout(
    title=f"Décomposition du score global ({total:.1f}/100)",
    yaxis=dict(title="Points", range=[0, 105]),
    height=380, margin=dict(t=50, b=20))
st.plotly_chart(fig_wf, use_container_width=True)

st.subheader("Pondérations du modèle")
pcol1, pcol2 = st.columns([1, 2])
with pcol1:
    fig_pie = go.Figure(go.Pie(
        labels=["Militaire", "Politique", "Énergétique"],
        values=[w["weight_military"], w["weight_political"], w["weight_energy"]],
        hole=0.4,
        marker_colors=["#E74C3C", "#3498DB", "#F39C12"],
    ))
    fig_pie.update_layout(height=280, margin=dict(t=20, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)
with pcol2:
    st.markdown("""
    | Composante | Poids | Rationnel |
    |---|---|---|
    | **Score Militaire** | 40% | Facteur direct de fermeture du détroit |
    | **Score Politique** | 30% | Signal d'escalade diplomatique |
    | **Score Énergétique** | 30% | Réaction de marché et pression logistique |

    > *Les pondérations peuvent être ajustées dans `config/parameters.yaml`.*
    """)

st.markdown("---")

# ---- Évolution historique des scores ----
st.subheader("Évolution historique des scores (reconstructe depuis indicateurs)")

daily     = data["daily"]
incidents = data["incidents"]

# Reconstruire la série énergie quotidienne
e_series = energy_score_series(daily, cfg)
energy_ts = pd.DataFrame({"date": daily["date"], "energy_score": e_series})

# Série militaire mensuelle → interpoler quotidien
m_series = military_score_series(incidents, cfg)
mil_ts = pd.DataFrame({
    "date": incidents["month_dt"],
    "military_score": m_series
})
mil_daily = (energy_ts[["date"]]
             .merge(mil_ts, on="date", how="left")
             .ffill().bfill())

# Global approx (sans political series complète, proxy constant)
pol_proxy = scores["political_score"]
global_ts = energy_ts.copy()
global_ts["military_score"] = mil_daily["military_score"].values
global_ts["global_score"] = global_ts.apply(
    lambda r: compute_global_score(
        r["military_score"] if pd.notna(r["military_score"]) else 0,
        pol_proxy, r["energy_score"], cfg), axis=1)

# Filtre 2 ans
cutoff = global_ts["date"].max() - pd.Timedelta(days=730)
ts = global_ts[global_ts["date"] >= cutoff]

fig_hist = go.Figure()
fig_hist.add_trace(go.Scatter(
    x=ts["date"], y=ts["energy_score"],
    name="Score Énergétique", line=dict(color="#F39C12", width=1.5)))
fig_hist.add_trace(go.Scatter(
    x=ts["date"], y=ts["military_score"],
    name="Score Militaire", line=dict(color="#E74C3C", width=1.5)))
fig_hist.add_trace(go.Scatter(
    x=ts["date"], y=ts["global_score"],
    name="Score Global", line=dict(color="#2C3E50", width=2.5)))
fig_hist.add_hrect(y0=65, y1=100, fillcolor="#E74C3C", opacity=0.06,
                   annotation_text="Zone C", annotation_position="right")
fig_hist.add_hrect(y0=35, y1=65, fillcolor="#F39C12", opacity=0.06,
                   annotation_text="Zone B", annotation_position="right")
fig_hist.add_hrect(y0=0, y1=35, fillcolor="#2ECC71", opacity=0.06,
                   annotation_text="Zone A", annotation_position="right")
fig_hist.update_layout(
    title="Évolution des scores — 2 dernières années",
    yaxis=dict(title="Score / 100", range=[0, 105]),
    height=400, legend=dict(orientation="h", y=1.02),
    margin=dict(t=50, b=20))
st.plotly_chart(fig_hist, use_container_width=True)

st.caption(
    "Note : le score politique est maintenu constant (proxy) car les sources NLP "
    "(Reuters, Bloomberg) nécessitent un accès API payant. "
    "Il peut être enrichi via une intégration NLP future.")
