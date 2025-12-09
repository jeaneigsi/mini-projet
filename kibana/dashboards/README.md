# Kibana Dashboards

Les dashboards Kibana doivent etre crees manuellement via l'interface Kibana puis exportes.

## Acces Kibana

URL: http://localhost:5601

## Index Pattern a creer

1. Aller dans Stack Management > Index Patterns
2. Creer un index pattern: `telemetry-*`
3. Selectionner `@timestamp` comme champ de temps

## Dashboards a creer

### 1. Overview Dashboard

**Visualisations:**
- Stat: Nombre total de sites
- Stat: Nombre total d'assets
- Pie Chart: Repartition par type d'asset (HVAC, CHILLER, ELEVATOR)
- Bar Chart: Volume de telemetrie par site
- Data Table: Derniers evenements

### 2. Site Detail Dashboard

**Variables:**
- site_code (dropdown)

**Visualisations:**
- Line Chart: temp_supply_air par asset HVAC
- Line Chart: water_temp_out par asset CHILLER
- Line Chart: motor_temp par asset ELEVATOR
- Gauge: vibration_level
- Metric: power_kw moyen

### 3. Alerts Dashboard

**Visualisations:**
- Timeline: Historique des depassements de seuils
- Heatmap: Intensite des anomalies par heure/jour
- Data Table: Metriques au-dessus des seuils

## Export des dashboards

Une fois crees, exporter via:
Stack Management > Saved Objects > Export

Sauvegarder les fichiers .ndjson dans ce dossier.
