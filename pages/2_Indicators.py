"""Page 2 — Suivi des indicateurs."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import last_n_days

st.set_page_config(page_title="Indicateurs — Ormuz", page_icon="📈", layout="wide")
st.title("📈 Suivi des Indicateurs")

if "data" not in st.session_state:
    st.warning("Rechargez l'application depuis la page d'accueil.")
    st.stop()

data    = st.session_state.data
scores  = st.session_state.scores

# ---- Sélecteur de période ----
period = st.sidebar.selectbox(
    "Période affichée", ["6 mois", "1 an", "2 ans", "5 ans", "Tout"], index=1
)
period_days = {"6 mois": 180, "1 an": 365, "2 ans": 730, "5 ans": 1825, "Tout": 99999}
n_days = period_days[period]

daily     = last_n_days(data["daily"], "date", n_days)
incidents = data["incidents"]

# ================================================================
# BLOC 1 — ÉNERGIE
# ================================================================
st.subheader("🛢️ Bloc Énergie")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Brent ($/b)",  f"{scores['brent_usd']:.1f}",
              delta=f"{scores['brent_7d_chg']:+.1f}% (7j)")
with c2:
    st.metric("WTI ($/b)",
              f"{daily['wti_usd'].iloc[-1]:.1f}")
with c3:
    st.metric("VIX", f"{scores['vix']:.1f}")

# Graphique Brent
fig_brent = go.Figure()
fig_brent.add_trace(go.Scatter(
    x=daily["date"], y=daily["brent_usd"],
    name="Brent", line=dict(color="#2980B9", width=2)))
if "brent_ma20" in daily.columns:
    fig_brent.add_trace(go.Scatter(
        x=daily["date"], y=daily["brent_ma20"],
        name="MA 20j", line=dict(color="#E67E22", width=1.5, dash="dot")))
fig_brent.update_layout(
    title="Prix du Brent (USD/baril)",
    yaxis_title="USD/b", height=320,
    legend=dict(orientation="h", y=1.02),
    margin=dict(t=40, b=20))
st.plotly_chart(fig_brent, use_container_width=True)

# Variation 7j
col_v1, col_v2 = st.columns(2)
with col_v1:
    if "brent_7d_change_pct" in daily.columns:
        fig_chg = go.Figure()
        chg = daily.dropna(subset=["brent_7d_change_pct"])
        colors = ["#E74C3C" if v > 0 else "#2ECC71" for v in chg["brent_7d_change_pct"]]
        fig_chg.add_trace(go.Bar(
            x=chg["date"], y=chg["brent_7d_change_pct"] * 100,
            marker_color=colors, name="Variation 7j (%)"))
        fig_chg.update_layout(title="Variation 7 jours Brent (%)",
                               yaxis_title="%", height=260,
                               margin=dict(t=40, b=20))
        st.plotly_chart(fig_chg, use_container_width=True)

with col_v2:
    fig_vix = go.Figure()
    fig_vix.add_trace(go.Scatter(
        x=daily["date"], y=daily["vix_close"],
        name="VIX", line=dict(color="#8E44AD", width=2), fill="tozeroy",
        fillcolor="rgba(142,68,173,0.1)"))
    fig_vix.add_hline(y=20, line_dash="dot", line_color="#F39C12",
                      annotation_text="Seuil 20", annotation_position="right")
    fig_vix.add_hline(y=30, line_dash="dot", line_color="#E74C3C",
                      annotation_text="Seuil 30", annotation_position="right")
    fig_vix.update_layout(title="VIX — Volatilité implicite globale",
                           yaxis_title="VIX", height=260,
                           margin=dict(t=40, b=20))
    st.plotly_chart(fig_vix, use_container_width=True)

st.markdown("---")

# ================================================================
# BLOC 2 — GÉOPOLITIQUE / CONFLITS
# ================================================================
st.subheader("⚔️ Bloc Géopolitique — Incidents UCDP (Golfe/Iran)")

gulf_countries = ["Iran", "Iraq", "Yemen", "Saudi Arabia", "United Arab Emirates",
                  "Oman", "Bahrain", "Kuwait", "Qatar"]
geo_gulf = data["geo"][data["geo"]["country"].isin(gulf_countries)].copy()
geo_gulf["month"] = geo_gulf["date_start"].dt.to_period("M").dt.to_timestamp()

inc = incidents.copy()

col_i1, col_i2 = st.columns(2)
with col_i1:
    # Incidents par mois
    fig_inc = go.Figure()
    fig_inc.add_trace(go.Bar(
        x=inc["month_dt"], y=inc["nb_incidents"],
        marker_color="#E74C3C", name="Nb incidents"))
    fig_inc.add_trace(go.Scatter(
        x=inc["month_dt"], y=inc["incidents_3m_avg"],
        name="Moyenne 3 mois", line=dict(color="#F39C12", width=2)))
    fig_inc.update_layout(title="Incidents militaires — Golfe/Iran (UCDP)",
                           yaxis_title="Nb incidents", height=320,
                           margin=dict(t=40, b=20))
    st.plotly_chart(fig_inc, use_container_width=True)

with col_i2:
    # Décès par mois
    fig_deaths = go.Figure()
    fig_deaths.add_trace(go.Bar(
        x=inc["month_dt"], y=inc["total_deaths"],
        marker_color="#8E44AD", name="Décès estimés"))
    fig_deaths.update_layout(title="Décès estimés — Golfe/Iran (UCDP)",
                              yaxis_title="Décès", height=320,
                              margin=dict(t=40, b=20))
    st.plotly_chart(fig_deaths, use_container_width=True)

# Carte événements récents
st.subheader("Événements récents — 90 derniers jours")
cutoff = data["geo"]["date_start"].max() - pd.Timedelta(days=90)
recent = data["geo"][data["geo"]["date_start"] >= cutoff].copy()

if len(recent) > 0 and "latitude" in recent.columns:
    fig_map = px.scatter_geo(
        recent,
        lat="latitude", lon="longitude",
        color="country",
        hover_name="conflict_name",
        hover_data={"date_start": True, "best": True, "country": False},
        size="best",
        size_max=20,
        projection="natural earth",
        title="Incidents géopolitiques récents (90j) — Moyen-Orient",
    )
    fig_map.update_geos(
        center=dict(lon=53, lat=27),
        projection_scale=4,
        showland=True, landcolor="#F5F5F0",
        showocean=True, oceancolor="#D6EAF8",
    )
    fig_map.update_layout(height=420, margin=dict(t=40, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

# Table événements récents
st.dataframe(
    recent[["date_start", "country", "conflict_name", "dyad_name",
            "best", "deaths_civilians", "where_description"]]
    .sort_values("date_start", ascending=False)
    .head(30)
    .rename(columns={
        "date_start": "Date", "country": "Pays",
        "conflict_name": "Conflit", "dyad_name": "Acteurs",
        "best": "Décès (estimé)", "deaths_civilians": "Civils",
        "where_description": "Lieu",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.subheader("🏦 Bloc Sanctions — OFAC Iran/Golfe")
sanctions = data["sanctions"]
st.metric("Entités sanctionnées (Iran/Golfe)", len(sanctions))
top_sanctions = sanctions[["name", "type", "country", "prog"]].head(20)
st.dataframe(top_sanctions.rename(columns={
    "name": "Entité", "type": "Type", "country": "Programmes", "prog": "Programme OFAC"
}), use_container_width=True, hide_index=True)
