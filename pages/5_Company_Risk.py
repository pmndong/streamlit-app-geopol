"""Page 5 — Impact Entreprises & Économie Française."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.company_risk import (
    get_top_exposed, get_sector_summary, get_impact_description,
    adjust_for_scenario, RISK_LABELS
)
from src.utils import risk_color

st.set_page_config(
    page_title="Impact Entreprises — Ormuz",
    page_icon="🏭",
    layout="wide",
)
st.title("🏭 Impact sur les Entreprises & l'Économie Française")
st.markdown(
    "Analyse de l'exposition des entreprises — avec focus sur les acteurs français "
    "et les canaux de transmission vers l'économie nationale."
)

if "companies" not in st.session_state:
    st.warning("Rechargez l'application depuis la page d'accueil.")
    st.stop()

entreprises   = st.session_state.companies
scores        = st.session_state.scores
scenario_dom  = st.session_state.dominant
cfg           = st.session_state.cfg

COULEURS_SCENARIO = {"A": "#2ECC71", "B": "#F39C12", "C": "#E74C3C"}
NOMS_SCENARIO = {
    "A": "Désescalade rapide",
    "B": "Tension contrôlée",
    "C": "Escalade régionale",
}

# ---- Bannière scénario courant ----
couleur_sc = COULEURS_SCENARIO[scenario_dom]
st.markdown(
    f"<div style='background:{couleur_sc}11;border-left:5px solid {couleur_sc};"
    f"padding:10px 16px;border-radius:6px;margin-bottom:16px'>"
    f"Scénario courant : <strong style='color:{couleur_sc}'>"
    f"Scénario {scenario_dom} — {NOMS_SCENARIO[scenario_dom]}</strong> "
    f"| Score global : <strong>{scores['global_score']:.0f}/100</strong> "
    f"| Brent : <strong>{scores['brent_usd']:.1f} $/b</strong>"
    f"</div>",
    unsafe_allow_html=True,
)

# ================================================================
# ONGLETS PRINCIPAUX
# ================================================================
onglet_fr, onglet_monde, onglet_detail = st.tabs([
    "🇫🇷 Focus Économie Française",
    "🌍 Classement Mondial",
    "🔍 Fiche Entreprise",
])

# ================================================================
# ONGLET 1 — FOCUS FRANCE
# ================================================================
with onglet_fr:
    st.subheader("Impact de la crise Ormuz sur l'économie française")

    df_fr = entreprises[entreprises["france_economy"] == 1].copy()

    # KPIs France
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Entreprises françaises / impact FR", len(df_fr))
    k2.metric("Niveau Critique", len(df_fr[df_fr["risk_level_adjusted"] == "Critique"]))
    k3.metric("Niveau Élevé",    len(df_fr[df_fr["risk_level_adjusted"] == "Élevé"]))
    k4.metric("Score moyen exposition", f"{df_fr['risk_adjusted'].mean()*100:.0f}/100")

    st.markdown("---")

    # ---- Canaux de transmission vers l'économie FR ----
    st.subheader("Canaux de transmission vers l'économie française")

    canaux = [
        {
            "titre": "⛽ Prix des carburants à la pompe",
            "description": (
                "Le prix du Brent est le principal déterminant du SP95 et du gasoil en France. "
                "Une hausse de 10 $/b se traduit par environ **+0,07 à 0,09 €/L** à la pompe. "
                "Impact direct sur le pouvoir d'achat des ménages et les coûts de transport."
            ),
            "acteurs": "TotalEnergies, stations-service françaises",
            "intensite": 0.90,
            "couleur": "#E74C3C",
        },
        {
            "titre": "🔥 Factures gaz et électricité",
            "description": (
                "L'approvisionnement en GNL via le Qatar (QatarEnergy) représente ~25% "
                "des importations d'Engie. Une fermeture d'Ormuz entraînerait une flambée "
                "du prix du gaz, répercutée sur les factures résidentielles et industrielles. "
                "L'électricité suit par le mécanisme de prix marginal."
            ),
            "acteurs": "Engie, EDF, TotalEnergies Marketing France",
            "intensite": 0.75,
            "couleur": "#E67E22",
        },
        {
            "titre": "🚚 Surcoûts logistiques & fret maritime",
            "description": (
                "CMA CGM (3e armateur mondial, Marseille) opère des routes Asie-Europe "
                "passant par le Golfe. La perturbation d'Ormuz implique des détournements "
                "via le Cap (+10 à 14 jours, +30 à 50% de fret). Répercussion sur le "
                "prix des biens importés."
            ),
            "acteurs": "CMA CGM, Geodis, XPO Logistics, La Poste/DPD",
            "intensite": 0.65,
            "couleur": "#F1C40F",
        },
        {
            "titre": "✈️ Surcharges carburant aviation",
            "description": (
                "Le kérosène représente 20-25% des coûts d'Air France-KLM. "
                "Une hausse prolongée du Brent se traduit par des surcharges carburant "
                "sur les billets et une pression sur les marges. "
                "Impact aussi sur easyJet qui opère depuis CDG, Nice, Lyon, Toulouse."
            ),
            "acteurs": "Air France-KLM, easyJet (France)",
            "intensite": 0.62,
            "couleur": "#3498DB",
        },
        {
            "titre": "🏭 Coûts de production industriels",
            "description": (
                "L'industrie française (chimie, automobile, BTP, métallurgie) est fortement "
                "dépendante du pétrole comme matière première (plastiques, résines, solvants) "
                "et comme énergie. Arkema, Michelin, ArcelorMittal Dunkerque/Fos sont "
                "particulièrement vulnérables."
            ),
            "acteurs": "Arkema, Michelin, Valeo, ArcelorMittal, Saint-Gobain, Lafarge",
            "intensite": 0.60,
            "couleur": "#8E44AD",
        },
        {
            "titre": "🌾 Agriculture & alimentation",
            "description": (
                "Triple impact pour l'agriculture française : (1) carburant agricole "
                "(fioul détaxé), (2) engrais azotés liés au prix du gaz, "
                "(3) surcoûts logistiques d'export des céréales. "
                "Risque d'inflation alimentaire."
            ),
            "acteurs": "InVivo/Soufflet, Danone, Carrefour",
            "intensite": 0.45,
            "couleur": "#27AE60",
        },
        {
            "titre": "🏗️ Secteur de la construction",
            "description": (
                "La hausse de l'énergie pèse sur les coûts de production du ciment "
                "et du verre. Saint-Gobain et Lafarge France voient leurs marges "
                "se comprimer, avec répercussion sur les prix de la construction neuve "
                "et de la rénovation."
            ),
            "acteurs": "Saint-Gobain, LafargeHolcim France",
            "intensite": 0.45,
            "couleur": "#95A5A6",
        },
        {
            "titre": "✈️ Carnet de commandes aéronautique",
            "description": (
                "Les compagnies du Golfe (Emirates, Qatar Airways, Etihad) sont parmi "
                "les plus gros clients d'Airbus et de Safran. Une crise prolongée "
                "réduit leur capacité d'investissement et peut entraîner des reports "
                "de commandes. Impact emploi à Toulouse et en Île-de-France."
            ),
            "acteurs": "Airbus, Safran, Thales",
            "intensite": 0.40,
            "couleur": "#16A085",
        },
    ]

    for canal in canaux:
        with st.expander(
            f"{canal['titre']} — Intensité : {canal['intensite']*100:.0f}/100",
            expanded=(canal["intensite"] >= 0.70),
        ):
            col_desc, col_bar = st.columns([3, 1])
            with col_desc:
                st.markdown(canal["description"])
                st.caption(f"**Acteurs concernés :** {canal['acteurs']}")
            with col_bar:
                pct = int(canal["intensite"] * 100)
                st.markdown(
                    f"<div style='text-align:center'>"
                    f"<div style='font-size:2em;font-weight:bold;color:{canal['couleur']}'>"
                    f"{pct}</div>"
                    f"<div style='font-size:.75em;color:#888'>/ 100</div>"
                    f"<div style='background:#eee;border-radius:4px;height:10px;margin-top:4px'>"
                    f"<div style='background:{canal['couleur']};width:{pct}%;height:100%;"
                    f"border-radius:4px'></div></div></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ---- Classement entreprises françaises ----
    st.subheader("🏆 Entreprises françaises — Classement par exposition")

    df_fr_sorted = df_fr.sort_values("risk_adjusted", ascending=False).reset_index(drop=True)

    couleurs_barres = [risk_color(r) for r in df_fr_sorted["risk_level_adjusted"]]
    fig_fr = go.Figure()
    fig_fr.add_trace(go.Bar(
        x=df_fr_sorted["risk_adjusted"] * 100,
        y=df_fr_sorted["company"],
        orientation="h",
        marker_color=couleurs_barres,
        text=[f"{v*100:.0f}" for v in df_fr_sorted["risk_adjusted"]],
        textposition="outside",
        customdata=df_fr_sorted[["sector", "risk_level_adjusted", "france_impact"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Secteur : %{customdata[0]}<br>"
            "Niveau : %{customdata[1]}<br>"
            "Score : %{x:.0f}/100<br>"
            "<extra>%{customdata[2]}</extra>"
        ),
    ))
    fig_fr.update_layout(
        xaxis=dict(title="Score d'exposition ajusté / 100", range=[0, 120]),
        yaxis=dict(autorange="reversed"),
        height=max(400, len(df_fr_sorted) * 22),
        margin=dict(t=20, b=20, l=220),
    )
    st.plotly_chart(fig_fr, use_container_width=True)

    st.markdown("---")

    # ---- Heatmap secteurs France ----
    st.subheader("Exposition par secteur — Périmètre France")
    sec_fr = get_sector_summary(df_fr, score_col="risk_adjusted")

    fig_sec_fr = go.Figure(go.Bar(
        x=sec_fr["avg_risk"] * 100,
        y=sec_fr["sector"],
        orientation="h",
        marker=dict(
            color=sec_fr["avg_risk"] * 100,
            colorscale=[[0, "#2ECC71"], [0.35, "#F1C40F"],
                        [0.55, "#E67E22"], [1.0, "#E74C3C"]],
            showscale=True,
            colorbar=dict(title="Score moyen"),
        ),
        text=[
            f"{v*100:.0f} | {n} entrep."
            for v, n in zip(sec_fr["avg_risk"], sec_fr["nb_companies"])
        ],
        textposition="outside",
    ))
    fig_sec_fr.update_layout(
        xaxis=dict(title="Score moyen / 100", range=[0, 120]),
        yaxis=dict(autorange="reversed"),
        height=max(300, len(sec_fr) * 30),
        margin=dict(t=10, b=20, l=260),
    )
    st.plotly_chart(fig_sec_fr, use_container_width=True)

    # ---- Impact France détaillé par entreprise ----
    st.subheader("Impacts France — Détail par entreprise")
    df_fr_impact = df_fr_sorted[df_fr_sorted["france_impact"].str.strip() != ""][
        ["company", "sector", "risk_adjusted", "risk_level_adjusted", "france_impact"]
    ].copy()
    df_fr_impact["risk_adjusted"] = (df_fr_impact["risk_adjusted"] * 100).round(1)
    st.dataframe(
        df_fr_impact.rename(columns={
            "company": "Entreprise",
            "sector": "Secteur",
            "risk_adjusted": "Score /100",
            "risk_level_adjusted": "Niveau",
            "france_impact": "Impact France",
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score /100": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=100, format="%.0f"
            ),
        },
    )


# ================================================================
# ONGLET 2 — CLASSEMENT MONDIAL
# ================================================================
with onglet_monde:
    st.subheader("Classement mondial — Toutes entreprises")

    # Filtres sidebar (affichés ici car onglets)
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tous_secteurs = sorted(entreprises["sector"].unique())
        secteurs_sel = st.multiselect(
            "Secteurs", tous_secteurs, default=tous_secteurs, key="secteurs_monde"
        )
    with col_f2:
        niveaux_sel = st.multiselect(
            "Niveau de risque",
            ["Critique", "Élevé", "Modéré", "Faible"],
            default=["Critique", "Élevé", "Modéré", "Faible"],
            key="niveaux_monde",
        )
    with col_f3:
        filtre_fr = st.checkbox("Seulement impact France", value=False)

    df_monde = entreprises[
        entreprises["sector"].isin(secteurs_sel)
        & entreprises["risk_level_adjusted"].isin(niveaux_sel)
    ]
    if filtre_fr:
        df_monde = df_monde[df_monde["france_economy"] == 1]

    # KPIs
    m1, m2, m3 = st.columns(3)
    m1.metric("Entreprises affichées", len(df_monde))
    m2.metric("Critiques", len(df_monde[df_monde["risk_level_adjusted"] == "Critique"]))
    m3.metric("Score moyen", f"{df_monde['risk_adjusted'].mean()*100:.0f}/100")

    # Top 15
    top15 = get_top_exposed(df_monde, n=15)
    couleurs_top = [risk_color(r) for r in top15["risk_level_adjusted"]]
    flag_fr = ["🇫🇷 " if f else "" for f in top15["france_economy"]]

    fig_top = go.Figure(go.Bar(
        x=top15["risk_adjusted"] * 100,
        y=[f"{flag}{c}" for flag, c in zip(flag_fr, top15["company"])],
        orientation="h",
        marker_color=couleurs_top,
        text=[f"{v*100:.0f}" for v in top15["risk_adjusted"]],
        textposition="outside",
        customdata=top15[["sector", "risk_level_adjusted"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>Secteur : %{customdata[0]}<br>"
            "Niveau : %{customdata[1]}<br>Score : %{x:.0f}/100<extra></extra>"
        ),
    ))
    fig_top.update_layout(
        xaxis=dict(title="Score d'exposition / 100", range=[0, 120]),
        yaxis=dict(autorange="reversed"),
        height=480,
        margin=dict(t=20, b=20, l=200),
    )
    st.plotly_chart(fig_top, use_container_width=True)

    # Heatmap tous secteurs
    st.subheader("Heatmap par secteur d'activité")
    sec_monde = get_sector_summary(df_monde, score_col="risk_adjusted")

    fig_heat = go.Figure(go.Bar(
        x=sec_monde["avg_risk"] * 100,
        y=sec_monde["sector"],
        orientation="h",
        marker=dict(
            color=sec_monde["avg_risk"] * 100,
            colorscale=[[0, "#2ECC71"], [0.35, "#F1C40F"],
                        [0.55, "#E67E22"], [1.0, "#E74C3C"]],
            showscale=True,
            colorbar=dict(title="Score moy."),
        ),
        text=[
            f"{v*100:.0f} | {n} entreprises"
            for v, n in zip(sec_monde["avg_risk"], sec_monde["nb_companies"])
        ],
        textposition="outside",
        customdata=sec_monde[["nb_companies", "nb_critique"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>Score moyen : %{x:.0f}/100<br>"
            "Nb entreprises : %{customdata[0]}<br>"
            "Critiques : %{customdata[1]}<extra></extra>"
        ),
    ))
    fig_heat.update_layout(
        xaxis=dict(title="Score moyen / 100", range=[0, 125]),
        yaxis=dict(autorange="reversed"),
        height=max(400, len(sec_monde) * 28),
        margin=dict(t=10, b=20, l=260),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Table complète
    st.subheader("Table complète")
    df_affichage = df_monde.sort_values("risk_adjusted", ascending=False).copy()
    df_affichage["Drap."] = df_affichage["france_economy"].map({1: "🇫🇷", 0: ""})
    df_affichage["risk_adjusted_100"]      = (df_affichage["risk_adjusted"] * 100).round(1)
    df_affichage["oil_dependency_100"]     = (df_affichage["oil_dependency_score"] * 100).round(0)
    df_affichage["hormuz_exposure_100"]    = (df_affichage["hormuz_exposure_score"] * 100).round(0)
    df_affichage["sector_sensitivity_100"] = (df_affichage["sector_sensitivity_score"] * 100).round(0)

    st.dataframe(
        df_affichage[[
            "Drap.", "company", "sector", "country", "ticker",
            "oil_dependency_100", "hormuz_exposure_100", "sector_sensitivity_100",
            "risk_adjusted_100", "risk_level_adjusted",
        ]].rename(columns={
            "Drap.": "FR",
            "company": "Entreprise",
            "sector": "Secteur",
            "country": "Pays",
            "ticker": "Ticker",
            "oil_dependency_100": "Dép. pétrole",
            "hormuz_exposure_100": "Exp. Ormuz",
            "sector_sensitivity_100": "Sens. sectorielle",
            "risk_adjusted_100": "Score /100",
            "risk_level_adjusted": "Niveau",
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score /100": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=100, format="%.0f"
            ),
        },
    )


# ================================================================
# ONGLET 3 — FICHE ENTREPRISE
# ================================================================
with onglet_detail:
    st.subheader("Fiche entreprise — Analyse détaillée")

    entreprise_sel = st.selectbox(
        "Sélectionner une entreprise",
        options=entreprises.sort_values("risk_adjusted", ascending=False)["company"].tolist(),
    )

    ligne = entreprises[entreprises["company"] == entreprise_sel].iloc[0]
    niveau  = ligne["risk_level_adjusted"]
    rc      = risk_color(niveau)
    impacts = get_impact_description(niveau)

    col_info, col_scores = st.columns([1, 1])
    with col_info:
        drapeau = "🇫🇷 " if ligne["france_economy"] == 1 else ""
        st.markdown(f"## {drapeau}{ligne['company']}")
        st.markdown(f"**Secteur :** {ligne['sector']}")
        st.markdown(f"**Pays :** {ligne['country']}")
        st.markdown(f"**Ticker :** {ligne['ticker']} ({ligne['exchange']})")

        st.markdown(
            f"<div style='background:{rc}22;border-left:4px solid {rc};"
            f"padding:12px;border-radius:6px;margin:12px 0'>"
            f"<b>Niveau de risque (scénario {scenario_dom}) :</b> "
            f"<span style='color:{rc};font-size:1.25em;font-weight:bold'>{niveau}</span><br>"
            f"<b>Score d'exposition :</b> {ligne['risk_adjusted']*100:.0f}/100 "
            f"<span style='color:#888;font-size:.85em'>"
            f"(baseline : {ligne['company_risk_score']*100:.0f}/100)</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("**Justification Ormuz :**")
        st.info(ligne["hormuz_exposure_rationale"])

        if ligne["france_economy"] == 1 and str(ligne.get("france_impact", "")).strip():
            st.markdown("**Impact économie française :**")
            st.success(ligne["france_impact"])

    with col_scores:
        composantes = {
            "Dépendance pétrole (50%)":       ligne["oil_dependency_score"],
            "Exposition Ormuz directe (30%)": ligne["hormuz_exposure_score"],
            "Sensibilité sectorielle (20%)":  ligne["sector_sensitivity_score"],
        }
        fig_comp = go.Figure(go.Bar(
            x=list(composantes.keys()),
            y=[v * 100 for v in composantes.values()],
            marker_color=[rc, rc, rc],
            text=[f"{v*100:.0f}" for v in composantes.values()],
            textposition="outside",
        ))
        fig_comp.update_layout(
            title="Décomposition du score d'exposition",
            yaxis=dict(range=[0, 115], title="/ 100"),
            height=300,
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("**Impacts potentiels sous ce scénario :**")
        for impact in impacts:
            st.markdown(f"- {impact}")

    # Comparaison avec secteur
    st.markdown("---")
    st.subheader("Comparaison au sein du secteur")
    meme_secteur = entreprises[entreprises["sector"] == ligne["sector"]].sort_values(
        "risk_adjusted", ascending=False
    )
    couleurs_secteur = [
        "#E74C3C" if c == entreprise_sel else risk_color(r)
        for c, r in zip(meme_secteur["company"], meme_secteur["risk_level_adjusted"])
    ]
    fig_secteur = go.Figure(go.Bar(
        x=meme_secteur["risk_adjusted"] * 100,
        y=meme_secteur["company"],
        orientation="h",
        marker_color=couleurs_secteur,
        text=[f"{v*100:.0f}" for v in meme_secteur["risk_adjusted"]],
        textposition="outside",
    ))
    fig_secteur.update_layout(
        title=f"Secteur : {ligne['sector']}",
        xaxis=dict(range=[0, 120], title="Score /100"),
        yaxis=dict(autorange="reversed"),
        height=max(200, len(meme_secteur) * 35),
        margin=dict(t=40, b=20, l=200),
    )
    st.plotly_chart(fig_secteur, use_container_width=True)

st.markdown("---")
st.caption(
    "Formule : Score = 0,5 × dépendance pétrole + 0,3 × exposition Ormuz + 0,2 × sensibilité sectorielle. "
    "Scores ajustés selon le scénario dominant courant (multiplicateur A=×0,70 / B=×1,00 / C=×1,35). "
    "Sources : rapports annuels, données sectorielles, analyse interne. "
    "Cet outil est un aide à la décision — pas un modèle de prédiction exacte."
)
