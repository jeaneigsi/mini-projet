# Kibana Dashboards

Dashboards préconfigurés pour la visualisation de la télémétrie Maintenance 4.0.

## Dashboards Inclus

### 1. `telemetry-overview.ndjson` - Vue Globale Télémétrie
- **Volume de Télémétrie** : Histogramme du nombre de documents par intervalle de temps
- **Répartition par Type d'Asset** : Donut chart (HVAC, CHILLER, ELEVATOR)
- **Répartition par Site** : Pie chart des données par site
- **Documents par Minute** : Métrique en temps réel

### 2. `equipment-metrics.ndjson` - Métriques Équipements
- **Température Soufflage HVAC** : Courbe temps réel par asset
- **Niveau de Vibration HVAC** : Courbe avec seuil visuel
- **Température Eau Glacée CHILLER** : Courbe temps réel
- **Température Moteur ELEVATOR** : Courbe avec limites
- **Puissance Consommée** : Area chart pour tous les équipements

## Import des Dashboards

### Méthode 1 : Via l'interface Kibana

1. Accéder à Kibana : http://localhost:5601
2. Aller dans **Stack Management** > **Saved Objects**
3. Cliquer sur **Import**
4. Sélectionner les fichiers `.ndjson` un par un
5. Cocher "Automatically overwrite conflicts" si nécessaire
6. Cliquer sur **Import**

### Méthode 2 : Via API (automatique)

```bash
# Import telemetry overview dashboard
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  --form file=@kibana/dashboards/telemetry-overview.ndjson

# Import equipment metrics dashboard
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  --form file=@kibana/dashboards/equipment-metrics.ndjson
```

## Accès aux Dashboards

Après import, les dashboards sont accessibles via :
- Menu hamburger > **Analytics** > **Dashboard**
- Ou directement : http://localhost:5601/app/dashboards

## Index Pattern

Les dashboards utilisent l'index pattern `telemetry-*` qui est créé automatiquement lors de l'import.

Si besoin de le créer manuellement :
1. **Stack Management** > **Data Views**
2. Créer un data view avec :
   - Name: `telemetry-*`
   - Index pattern: `telemetry-*`
   - Timestamp field: `@timestamp`

## Structure des Données Attendues

Les dashboards s'attendent à des documents Elasticsearch avec cette structure :

```json
{
  "@timestamp": "2024-01-01T12:00:00Z",
  "site_code": "CAS-S1",
  "asset_code": "CAS-S1-HVAC_1",
  "asset_type": "HVAC",
  "metrics": {
    "temp_supply_air": 17.5,
    "temp_out_air": 32.0,
    "vibration_level": 3.2,
    "power_kw": 12.5,
    "water_temp_out": 12.0,
    "motor_temp": 45.0,
    "door_cycles": 50000,
    "run_hours": 250
  }
}
```

## Personnalisation

Pour modifier les dashboards :
1. Ouvrir le dashboard dans Kibana
2. Cliquer sur **Edit**
3. Modifier les visualisations
4. Sauvegarder
5. Exporter via **Stack Management** > **Saved Objects** > **Export**
