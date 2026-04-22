import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

dest_ref = 'C:/Users/papam/Documents/AnalystGeoPol/Données/reference'

# Format : (entreprise, secteur, pays, ticker, bourse,
#           justification_ormuz, oil_dep, hormuz_exp, sector_sens,
#           flag_france, impact_france)
# flag_france : 1 = entreprise française OU avec impact direct sur économie FR

entreprises = [
    # ================================================
    # PÉTROLE & GAZ — MAJORS
    # ================================================
    ('TotalEnergies', 'Pétrole & Gaz — Major intégrée', 'France', 'TTE', 'Euronext Paris',
     'Production au Qatar, Iraq, UAE. ~35% du brut TotalEnergies transite par Ormuz. '
     'Leader du CAC40 en exposition directe.',
     0.90, 0.85, 0.95, 1,
     'Pression sur marges amont + hausse prix carburant en France. '
     '1er contributeur CAC40 aux bénéfices énergétiques.'),
    ('BP', 'Pétrole & Gaz — Major intégrée', 'Royaume-Uni', 'BP', 'LSE',
     'Partenariats Gulf (Iraq, UAE). ~15% production transit Ormuz.',
     0.85, 0.80, 0.90, 0,
     'Impact indirect via prix brut mondial.'),
    ('Shell', 'Pétrole & Gaz — Major intégrée', 'Pays-Bas', 'SHEL', 'LSE/Euronext',
     'Contrats LNG Qatar (QatarEnergy). Fort transit Ormuz.',
     0.85, 0.80, 0.90, 0,
     'Impact indirect via prix LNG et brut.'),
    ('ExxonMobil', 'Pétrole & Gaz — Major intégrée', 'États-Unis', 'XOM', 'NYSE',
     'Opérations Iraq (West Qurna). Exposition modérée.',
     0.75, 0.70, 0.80, 0,
     'Aucun impact direct sur économie FR.'),
    ('Saudi Aramco', 'Pétrole & Gaz — Major intégrée', 'Arabie Saoudite', '2222', 'Tadawul',
     '100% des exportations passent par Ormuz. Exposition maximale.',
     1.00, 1.00, 1.00, 0,
     'Perturbation des exportations saoudiennes = hausse immédiate des prix mondiaux.'),
    ('QatarEnergy', 'Pétrole & Gaz — Major intégrée', 'Qatar', 'Non coté', '—',
     'LNG Qatar 100% via Ormuz. TotalEnergies = partenaire stratégique.',
     1.00, 1.00, 1.00, 1,
     'Perturbation LNG Qatar = impact direct sur approvisionnement Engie + TotalEnergies FR.'),
    ('Adnoc', 'Pétrole & Gaz — Major intégrée', 'Émirats Arabes Unis', 'Partiel', '—',
     'Exportations UAE via Ormuz (pipeline ADCO alternatif limité).',
     0.90, 0.90, 0.95, 0, ''),
    ('Eni', 'Pétrole & Gaz — Major intégrée', 'Italie', 'ENI', 'Borsa Italiana',
     'Présence Iraq, UAE. Exposition modérée.',
     0.70, 0.65, 0.80, 0, ''),
    ('Equinor', 'Pétrole & Gaz — Major intégrée', 'Norvège', 'EQNR', 'Oslo Bors',
     'Production mer du Nord. Peu exposée Ormuz.',
     0.30, 0.20, 0.40, 0, ''),

    # ================================================
    # PÉTROLE & GAZ — RAFFINAGE / DISTRIBUTION
    # ================================================
    ('Repsol', 'Pétrole & Gaz — Raffinage', 'Espagne', 'REP', 'BME',
     'Imports brut Moyen-Orient pour raffinage. Voisin économique FR.',
     0.65, 0.60, 0.70, 0, ''),
    ('Valero Energy', 'Pétrole & Gaz — Raffinage', 'États-Unis', 'VLO', 'NYSE',
     'Importe brut moyen-oriental. Marges impactées.',
     0.55, 0.50, 0.60, 0, ''),

    # ================================================
    # TRANSPORT MARITIME — TANKERS
    # ================================================
    ('Frontline', 'Transport Maritime — Tankers', 'Norvège', 'FRO', 'NYSE/Oslo',
     'Flotte VLCC routes Golfe Persique. Impact direct fermeture Ormuz.',
     0.95, 0.95, 0.90, 0,
     'Hausse des taux de fret tankers = renchérissement import brut FR.'),
    ('Euronav', 'Transport Maritime — Tankers', 'Belgique', 'EURN', 'NYSE/Euronext',
     'VLCC routes Golfe. Impact fermeture Ormuz majeur.',
     0.95, 0.95, 0.90, 0,
     'Même impact indirect sur coût d\'import brut France.'),
    ('Teekay Corporation', 'Transport Maritime — Tankers', 'Bermudes', 'TK', 'NYSE',
     'Tankers Moyen-Orient. Impact fermeture majeur.',
     0.90, 0.90, 0.85, 0, ''),
    ('DHT Holdings', 'Transport Maritime — Tankers', 'Bermudes', 'DHT', 'NYSE/Oslo',
     'VLCC routes Golfe Persique.',
     0.90, 0.90, 0.85, 0, ''),

    # ================================================
    # TRANSPORT MARITIME — CONTENEURS
    # ================================================
    ('CMA CGM', 'Transport Maritime — Conteneurs', 'France', 'Non coté', '—',
     'Routes Asie-Europe passant par Golfe. Détournements coûteux si fermeture Ormuz.',
     0.40, 0.35, 0.50, 1,
     '3e armateur mondial, basé à Marseille. Surcoûts fret répercutés sur importateurs FR. '
     'Impacts prix biens de consommation en France.'),
    ('Maersk', 'Transport Maritime — Conteneurs', 'Danemark', 'MAERSK-B', 'Nasdaq Copenhague',
     'Leader conteneurs mondial. Impact surcoûts fret et détournements.',
     0.40, 0.35, 0.50, 0,
     'Hausse fret maritime = inflation importations FR.'),
    ('Hapag-Lloyd', 'Transport Maritime — Conteneurs', 'Allemagne', 'HLAG', 'XETRA',
     'Routes Asie-Europe. Perturbation logistique.',
     0.40, 0.35, 0.50, 0, ''),

    # ================================================
    # AVIATION
    # ================================================
    ('Air France-KLM', 'Aviation', 'France', 'AF', 'Euronext Paris',
     'Carburant = 20-25% des coûts. Hausse Brent +10% → impact marge direct. '
     'Passager emblématique du CAC40.',
     0.70, 0.20, 0.85, 1,
     'Surcharges carburant, hausse prix billets. Impact direct compétitivité et tourisme FR. '
     'Risque de perturbation des routes moyen-orientales (Dubai, Doha).'),
    ('Lufthansa Group', 'Aviation', 'Allemagne', 'LHA', 'XETRA',
     'Très sensible prix kérosène. Concurrent direct AF sur routes FR.',
     0.70, 0.20, 0.85, 0,
     'Impact indirect concurrence sur routes internationales depuis France.'),
    ('Emirates', 'Aviation', 'Émirats Arabes Unis', 'Non coté', '—',
     'Hub Dubai dans la zone de crise. Perturbation des correspondances.',
     0.95, 0.60, 0.95, 0,
     'Perturbation connexions Europe-Asie via Dubai = surcharge pour voyageurs FR.'),
    ('Ryanair', 'Aviation', 'Irlande', 'RYA', 'Euronext/Nasdaq',
     'Peu exposée géo. Très sensible carburant (30% des coûts).',
     0.50, 0.05, 0.80, 0,
     'Hausse billets low-cost = impact pouvoir d\'achat voyageurs FR.'),
    ('easyJet', 'Aviation', 'Royaume-Uni', 'EZJ', 'LSE',
     'Sensibilité carburant élevée. Opère depuis aéroports français.',
     0.50, 0.05, 0.78, 1,
     'Opère CDG, Nice, Lyon, Toulouse. Surcharges carburant sur routes FR internes/EU.'),

    # ================================================
    # RAFFINERIES & DISTRIBUTION CARBURANT (FRANCE)
    # ================================================
    ('TotalEnergies Raffinage', 'Pétrole & Gaz — Raffinage France', 'France', 'TTE', 'Euronext Paris',
     'Raffineries françaises (Normandie, Donges, Feyzin, Provence). '
     'Approvisionnement brut Moyen-Orient ~30% du mix.',
     0.75, 0.65, 0.85, 1,
     'Pénurie ou renchérissement brut ME → tension sur prix carburants français (SP95, gasoil). '
     'Impact direct inflation énergétique des ménages et entreprises FR.'),

    # ================================================
    # PÉTROCHIMIE & CHIMIE
    # ================================================
    ('BASF', 'Pétrochimie & Chimie', 'Allemagne', 'BAS', 'XETRA',
     'Feedstock naphta/gazole dérivé brut. Coûts énergétiques très sensibles.',
     0.65, 0.50, 0.70, 0,
     'Fournisseur de l\'industrie automobile et chimique française.'),
    ('Arkema', 'Pétrochimie & Chimie', 'France', 'AKE', 'Euronext Paris',
     'Spécialités chimiques. Matières premières pétrosourcées (éthylène, propylène). '
     'Issu de TotalEnergies.',
     0.65, 0.55, 0.70, 1,
     'Hausse feedstock = pression marges Arkema. Répercussion sur clients industriels FR '
     '(cosmétique, emballage, construction).'),
    ('Solvay', 'Pétrochimie & Chimie', 'Belgique', 'SOLB', 'Euronext Bruxelles',
     'Chimie spécialisée, matériaux avancés. Dépendance pétrochimique.',
     0.60, 0.45, 0.65, 0, ''),
    ('SABIC', 'Pétrochimie & Chimie', 'Arabie Saoudite', 'SABIC', 'Tadawul',
     'Filiale Aramco. 100% exposée Ormuz.',
     1.00, 1.00, 0.95, 0, ''),
    ('Air Liquide', 'Pétrochimie & Chimie', 'France', 'AI', 'Euronext Paris',
     'Gaz industriels. Énergie = 40% des coûts opérationnels. '
     'Sensible hausse prix gaz/électricité liée au choc pétrolier.',
     0.40, 0.30, 0.65, 1,
     'Hausse coûts de production répercutée sur industries FR (sidérurgie, chimie, alimentation). '
     'Impact compétitivité industrielle française.'),

    # ================================================
    # AUTOMOBILE & MANUFACTURIERS FRANCE
    # ================================================
    ('Stellantis', 'Automobile', 'Pays-Bas/France', 'STLA', 'NYSE/Euronext',
     'Plastics/résines pétrosourcées. Coûts production impactés. '
     'Sites français : Sochaux, Poissy, Rennes.',
     0.50, 0.30, 0.55, 1,
     'Hausse résines plastiques/caoutchouc synthétique = surcoûts production FR. '
     'Risque compétitivité Peugeot/Citroën/Opel.'),
    ('Renault Group', 'Automobile', 'France', 'RNO', 'Euronext Paris',
     'Consommation matières pétrosourcées. Hausse coûts logistiques.',
     0.50, 0.25, 0.55, 1,
     'Surcoûts matières + logistique = pression marges usines FR (Flins, Douai, Maubeuge). '
     'Impact emploi industriel France.'),
    ('Michelin', 'Automobile — Équipementier', 'France', 'ML', 'Euronext Paris',
     'Caoutchouc synthétique = 40% butadiène (dérivé pétrole). '
     'Très sensible à la hausse des naphtas.',
     0.70, 0.55, 0.75, 1,
     'Hausse matières premières = pression marges Michelin. '
     'Risque hausse prix pneumatiques pour flotte de transport FR. '
     'Impact indirect sur coût logistique national.'),
    ('Valeo', 'Automobile — Équipementier', 'France', 'FR', 'Euronext Paris',
     'Composants auto. Plastiques, résines, câblages pétrosourcés.',
     0.55, 0.35, 0.60, 1,
     'Hausse inputs pétrosourcés = pression marges équipementier FR. '
     'Transmission aux constructeurs via prix pièces.'),
    ('Volkswagen Group', 'Automobile', 'Allemagne', 'VOW3', 'XETRA',
     'Inputs pétrosourcés + carburant. Moins exposé géo Ormuz.',
     0.45, 0.25, 0.50, 0,
     'Impact indirect via compétition avec marques FR.'),
    ('Toyota', 'Automobile', 'Japon', 'TM', 'TSE/NYSE',
     'Japon dépend ~90% brut Golfe. Supply chain très exposée.',
     0.70, 0.30, 0.70, 0, ''),

    # ================================================
    # UTILITIES & ÉNERGIE FRANCE
    # ================================================
    ('Engie', 'Utilities — Énergie', 'France', 'ENGI', 'Euronext Paris',
     'Import GNL dont ~25% Qatar (QatarEnergy). Exposition Ormuz via prix gaz. '
     'Distributeur gaz résidentiel et industriel en France.',
     0.55, 0.50, 0.60, 1,
     'Perturbation GNL Qatar = hausse prix gaz en France. '
     'Impact direct sur factures ménages et industriels FR. '
     'TotalEnergies = concurrent/partenaire sur LNG.'),
    ('EDF', 'Utilities — Énergie', 'France', 'EDF', 'Euronext Paris',
     'Nucléaire dominant. Pétrole/gaz dans le mix thermique résiduel + filiales.',
     0.25, 0.20, 0.30, 1,
     'Impact limité sur nucléaire. Mais hausse gaz = pression sur prix de l\'électricité '
     'en période de pointe (mécanisme de prix marginal). Impact indirect consommateurs FR.'),
    ('TotalEnergies Marketing France', 'Utilities — Distribution carburant', 'France', 'TTE', 'Euronext Paris',
     'Réseau de stations-service. Prix carburant à la pompe directement lié au Brent.',
     0.85, 0.75, 0.90, 1,
     'Hausse Brent +10% = hausse prix pompe ~+0.08 €/L en France. '
     'Impact pouvoir d\'achat ménages, coûts agriculteurs, transporteurs FR.'),

    # ================================================
    # TRANSPORT & LOGISTIQUE FRANCE
    # ================================================
    ('SNCF Voyageurs', 'Transport — Ferroviaire', 'France', 'Non coté', '—',
     'Carburant (diesel) = coût majeur. Électricité sensible hausse gaz.',
     0.45, 0.20, 0.60, 1,
     'Hausse prix diesel/électricité = pression sur tarification SNCF. '
     'Risque de répercussion sur prix billets ou déficit opérateur public.'),
    ('XPO Logistics France', 'Transport — Routier & Logistique', 'France/USA', 'XPO', 'NYSE',
     'Carburant diesel = 25-30% des coûts d\'exploitation transport routier.',
     0.60, 0.20, 0.75, 1,
     'Hausse gasoil = surcoûts logistique pour distributeurs et industriels FR. '
     'Transmission via surcharges carburant sur toute la chaîne.'),
    ('Geodis (filiale SNCF)', 'Transport — Routier & Logistique', 'France', 'Non coté', '—',
     'Opérateur logistique majeur France. Diesel = coût variable principal.',
     0.60, 0.20, 0.75, 1,
     'Hausse gasoil = surcoûts supply chain France. '
     'Clients : grandes surfaces, industrie, e-commerce.'),
    ('La Poste / DPD France', 'Transport — Colis & Livraison', 'France', 'Non coté', '—',
     'Flotte motorisée. Carburant = 15-20% des coûts d\'exploitation.',
     0.50, 0.15, 0.65, 1,
     'Hausse carburant = surcoût livraison, impact e-commerce et services postaux FR.'),
    ('CMA CGM', 'Transport Maritime — Conteneurs', 'France', 'Non coté', '—',
     'Routes Asie-Europe passant par Golfe. Détournements coûteux.',
     0.40, 0.35, 0.50, 1,
     '3e armateur mondial. Surcoûts fret = hausse prix importations FR '
     '(électronique, textile, matières premières).'),

    # ================================================
    # AGROALIMENTAIRE & GRANDE DISTRIBUTION FRANCE
    # ================================================
    ('Carrefour', 'Grande Distribution', 'France', 'CA', 'Euronext Paris',
     'Carburant logistique + plastiques emballage + matières pétrosourcées.',
     0.35, 0.15, 0.55, 1,
     'Surcoûts logistiques et emballages répercutés sur prix rayons. '
     'Impact direct sur inflation alimentaire en France. '
     'Risque de ruptures d\'approvisionnement produits importés.'),
    ('Danone', 'Agroalimentaire', 'France', 'BN', 'Euronext Paris',
     'Emballages plastiques + logistique. Sensibilité indirecte.',
     0.30, 0.15, 0.45, 1,
     'Hausse plastiques/emballages = pression marges Danone. '
     'Transmission partielle sur prix produits laitiers/nutrition FR.'),
    ('Yara International', 'Agroalimentaire — Engrais', 'Norvège', 'YAR', 'Oslo Bors',
     'Engrais azotés = gaz naturel. Hausse gaz → hausse coûts.',
     0.55, 0.40, 0.60, 0,
     'Hausse prix engrais = coût supplémentaire agriculture française. '
     'Impact filière céréales, maïs, betterave.'),
    ('InVivo / Soufflet', 'Agroalimentaire — Négoce céréales', 'France', 'Non coté', '—',
     'Carburant agricole + coûts logistiques + prix engrais.',
     0.45, 0.20, 0.55, 1,
     'Triple impact : hausse carburant agricole, hausse engrais (gaz), hausse fret export. '
     'Risque compétitivité céréales françaises sur marchés mondiaux.'),

    # ================================================
    # BTP & MATÉRIAUX DE CONSTRUCTION
    # ================================================
    ('Saint-Gobain', 'BTP & Matériaux', 'France', 'SGO', 'Euronext Paris',
     'Énergie = 15-20% des coûts de production (verre, plâtre, isolation). '
     'Gaz = intrant principal de fabrication.',
     0.40, 0.30, 0.60, 1,
     'Hausse gaz = surcoûts industriels Saint-Gobain. '
     'Répercussion sur coûts de construction en France. Impact BTP.'),
    ('LafargeHolcim France', 'BTP & Matériaux', 'France/Suisse', 'HOLN', 'SIX Swiss Exchange',
     'Ciment = énergie intensive (gaz + fuel lourd). Très sensible coûts énergie.',
     0.50, 0.35, 0.65, 1,
     'Hausse énergie = surcoûts ciment. Transmission sur prix construction neuve et infra FR. '
     'Impact projets BTP et rénovation.'),

    # ================================================
    # DÉFENSE & AÉRONAUTIQUE (FRANCE)
    # ================================================
    ('Airbus', 'Aéronautique & Défense', 'France/Allemagne', 'AIR', 'Euronext Paris',
     'Aluminium, titane, matériaux composites. Chaîne d\'approvisionnement mondiale. '
     'Clients compagnies aériennes du Golfe (Emirates, Qatar Airways).',
     0.35, 0.30, 0.45, 1,
     'Perturbation Ormuz = réduction commandes compagnies Golfe (clients majeurs Airbus). '
     'Risque de retard livraisons et tension sur carnet de commandes. '
     'Impact emploi aéronautique FR (Toulouse, Bordeaux).'),
    ('Safran', 'Aéronautique & Défense', 'France', 'SAF', 'Euronext Paris',
     'Moteurs et équipements aéronautiques. Dépendance matériaux stratégiques.',
     0.30, 0.25, 0.40, 1,
     'Baisse trafic aérien Moyen-Orient = impact carnet commandes moteurs CFM. '
     'Risque induit sur emploi FR (Ile-de-France, Occitanie).'),
    ('Thales', 'Aéronautique & Défense', 'France', 'HO', 'Euronext Paris',
     'Défense, sécurité maritime. Demande de systèmes de surveillance Ormuz potentielle.',
     0.15, 0.20, 0.25, 1,
     'Hausse tensions = opportunité pour contrats défense/sécurité maritime. '
     'Risque géopolitique sur contrats avec pays du Golfe.'),

    # ================================================
    # BANQUES & ASSURANCES (FRANCE)
    # ================================================
    ('BNP Paribas', 'Finance — Banque', 'France', 'BNP', 'Euronext Paris',
     'Financement trade (lettres de crédit pétrole), exposition trading énergie, '
     'portefeuilles entreprises exposées.',
     0.30, 0.25, 0.45, 1,
     'Hausse risque crédit clients exposés (pétroliers, transporteurs). '
     'Provisions potentielles. Impact activité trade finance pétrole. '
     'Risque de marché sur portefeuilles obligataires pays Golfe.'),
    ('Société Générale', 'Finance — Banque', 'France', 'GLE', 'Euronext Paris',
     'Financement matières premières. Desk commodity trading.',
     0.25, 0.20, 0.40, 1,
     'Exposition trading commodities. Volatilité accrue = opportunité et risque. '
     'Provisions secteurs exposés.'),
    ('AXA', 'Finance — Assurance', 'France', 'CS', 'Euronext Paris',
     'Assurance maritime, assurance transport, couverture risques industriels.',
     0.25, 0.30, 0.35, 1,
     'Hausse sinistralité maritime (zone guerre Ormuz). '
     'Pression primes assurance transport → transmission sur coûts entreprises FR. '
     'Risque de dépréciation portefeuilles obligataires pays Golfe.'),

    # ================================================
    # ACIER & INDUSTRIE LOURDE
    # ================================================
    ('ArcelorMittal France', 'Acier & Industrie Lourde', 'Luxembourg/France', 'MT', 'NYSE/Euronext',
     'Consommation gaz et énergie très élevée. Sensibilité coûts énergétiques.',
     0.50, 0.40, 0.55, 1,
     'Sites de Dunkerque, Fos-sur-Mer. Hausse gaz = surcoûts production acier FR. '
     'Risque fermeture temporaire comme 2021-22.'),
]

colonnes = [
    'entreprise', 'secteur', 'pays', 'ticker', 'bourse',
    'justification_ormuz',
    'dependance_petrole',
    'exposition_ormuz',
    'sensibilite_sectorielle',
    'economie_france',
    'impact_france'
]

df = pd.DataFrame(entreprises, columns=colonnes)

# Score entreprise = 0.5×dep_petrole + 0.3×exp_ormuz + 0.2×sens_sectorielle
df['score_exposition'] = (
    0.5 * df['dependance_petrole'] +
    0.3 * df['exposition_ormuz'] +
    0.2 * df['sensibilite_sectorielle']
).round(3)

def niveau_risque(s):
    if s >= 0.75: return 'Critique'
    elif s >= 0.55: return 'Élevé'
    elif s >= 0.35: return 'Modéré'
    else: return 'Faible'

df['niveau_risque'] = df['score_exposition'].apply(niveau_risque)
df = df.sort_values(['secteur', 'score_exposition'], ascending=[True, False])

# Renommer pour compatibilité avec src/company_risk.py
df_compat = df.rename(columns={
    'entreprise': 'company',
    'secteur': 'sector',
    'pays': 'country',
    'ticker': 'ticker',
    'bourse': 'exchange',
    'justification_ormuz': 'hormuz_exposure_rationale',
    'dependance_petrole': 'oil_dependency_score',
    'exposition_ormuz': 'hormuz_exposure_score',
    'sensibilite_sectorielle': 'sector_sensitivity_score',
    'score_exposition': 'company_risk_score',
    'niveau_risque': 'risk_level',
    'economie_france': 'france_economy',
    'impact_france': 'france_impact',
})

df_compat.to_csv(f'{dest_ref}/company_exposure_typologies.csv', index=False, encoding='utf-8-sig')

print(f'Entreprises totales : {len(df_compat)}')
print(f'Entreprises françaises / impact France : {df_compat["france_economy"].sum()}')
print()
print('Par secteur :')
print(df_compat.groupby('sector')['company'].count().sort_values(ascending=False).to_string())
print()
print('TOP 10 plus exposées :')
top = df_compat.nlargest(10, 'company_risk_score')[['company','sector','company_risk_score','risk_level','france_economy']]
print(top.to_string())
print()
print('TOP entreprises françaises :')
fr = df_compat[df_compat['france_economy']==1].nlargest(10,'company_risk_score')[['company','sector','company_risk_score','risk_level']]
print(fr.to_string())
