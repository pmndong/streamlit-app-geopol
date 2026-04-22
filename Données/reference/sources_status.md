# Statut des Sources de Données — App Risque Ormuz

## ✅ SOURCES INTÉGRÉES (open / téléchargées)

| Source | Données | Fichier local | Fréquence |
|--------|---------|---------------|-----------|
| **EIA** (U.S. Energy Information Administration) | Prix Brent spot, Prix WTI | `raw/energy/brent_daily_eia.xls`, `wti_daily_eia.xls` | Quotidien |
| **CBOE** | VIX (volatilité implicite) | `raw/energy/vix_daily_cboe.csv` | Quotidien |
| **UCDP** v26 (Uppsala Conflict Data Program) | Incidents militaires Moyen-Orient, décès estimés | `raw/conflits/ucdp_ged_candidate_v26.csv` | Mensuel (mis à jour ~2 semaines de retard) |
| **UCDP PRIO ACD** | Dataset conflits armés | `raw/conflits/ucdp_prio_acd_v251.zip` | Annuel |
| **OFAC** (U.S. Treasury) | Liste SDN sanctions (18 759 entités) | `raw/sanctions/sdn_ofac.csv` | Irrégulier (après chaque paquet de sanctions) |
| **OFAC filtré** | Entités Iran/Golfe uniquement (2 456) | `raw/sanctions/ofac_iran_gulf_filtered.csv` | Dérivé OFAC |

---

## ⚠️ SOURCES PARTIELLEMENT ACCESSIBLES

| Source | Problème | Alternative utilisée |
|--------|----------|---------------------|
| **EIA API v2** (données Brent/WTI structurées) | API key requise (gratuite mais enregistrement nécessaire) | Téléchargement XLS direct |
| **ACLED** (Armed Conflict Location & Event Data) | Enregistrement gratuit requis sur acleddata.com avant accès API | UCDP GED (couverture similaire Moyen-Orient) |
| **UCDP GED** | Candidat (dernières semaines) avec retard ~2 semaines | Données à jour jusqu'au 31 mars 2026 |

---

## ❌ SOURCES INACCESSIBLES / PAYANTES

| Source | Données voulues | Statut | Coût estimé |
|--------|----------------|--------|-------------|
| **MarineTraffic / Kpler** | Trafic maritime Ormuz, nombre de navires, AIS | Payant — API sur devis | +++ |
| **Clarksons Research** | Temps de transit, taux de fret tankers | Payant | +++ |
| **CME Group** | Volatilité options pétrole (OVX) | API payante ou data provider | + |
| **S&P Global** | Indice énergie global sectoriel | Payant | +++ |
| **IEA** (International Energy Agency) | Flux pétroliers Ormuz (volume) | Rapports gratuits, données structurées payantes | ++ |
| **UKMTO** (UK Maritime Trade Operations) | Incidents maritimes Golfe — attaques/saisies | Site accessible (403 depuis scripts), données non structurées | — |
| **Reuters / Bloomberg** | Articles NLP (sentiment, escalade) | Payant (API) | +++ |
| **Bloomberg Terminal** | Indices sectoriels MSCI, classement secteur | Licence institutionnelle | ++++ |

---

## 🔧 PROXIES UTILISÉS DANS L'APPLICATION

| Indicateur manquant | Proxy retenu | Qualité |
|---------------------|-------------|---------|
| Trafic maritime Ormuz | Non disponible — score logistique non calculé (prévu pour v2) | Faible |
| Score NLP (sentiment news) | UCDP political events (Iran/Liban/Yémen) = proxy d'intensité politique | Moyen |
| Volatilité pétrole (OVX) | VIX (corrélée mais imparfaite) | Moyen |
| Flux pétroliers IEA | Approximé via prix Brent + incidents | Faible |

---

## 📋 ACTIONS RECOMMANDÉES (v2)

1. **Enregistrement ACLED** (gratuit) → acleddata.com/register → remplace proxy UCDP avec données géolocalisées en temps réel
2. **EIA API key** (gratuit) → api.eia.gov → actualisation automatique Brent/WTI
3. **MarineTraffic / Kpler** → contacter pour tarif API "recherche" → données trafic Ormuz précises
4. **NLP RSS gratuits** → Al Jazeera / Reuters RSS → scoring sentiment via transformers gratuits (FinBERT ou CamemBERT)
