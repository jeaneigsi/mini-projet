-- =============================================
-- Maintenance 4.0 Platform - Database Schema
-- =============================================

-- Sites table
CREATE TABLE sites (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assets table
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('HVAC', 'CHILLER', 'ELEVATOR')),
    site_id INTEGER REFERENCES sites(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'OK' CHECK (status IN ('OK', 'WARNING', 'CRITICAL')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Maintenance Policies table
CREATE TABLE maintenance_policies (
    id SERIAL PRIMARY KEY,
    asset_type VARCHAR(20) NOT NULL,
    metric VARCHAR(50) NOT NULL,
    rule_type VARCHAR(20) NOT NULL CHECK (rule_type IN ('threshold', 'runtime', 'rate_of_change')),
    threshold FLOAT NOT NULL,
    condition VARCHAR(5) NOT NULL CHECK (condition IN ('>', '<', '>=', '<=', '=')),
    window_minutes INTEGER,
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),
    description TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    policy_id INTEGER REFERENCES maintenance_policies(id) ON DELETE SET NULL,
    triggered_at TIMESTAMP DEFAULT NOW(),
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),
    status VARCHAR(10) DEFAULT 'open' CHECK (status IN ('open', 'ack', 'closed')),
    message TEXT NOT NULL,
    metric_value FLOAT,
    acknowledged_at TIMESTAMP,
    closed_at TIMESTAMP
);

-- Work Orders table
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'done', 'cancelled')),
    priority VARCHAR(10) DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
    assigned_to VARCHAR(100),
    notes TEXT
);

-- Indexes for performance
CREATE INDEX idx_assets_site_id ON assets(site_id);
CREATE INDEX idx_assets_type ON assets(type);
CREATE INDEX idx_alerts_asset_id ON alerts(asset_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_work_orders_status ON work_orders(status);
CREATE INDEX idx_work_orders_alert_id ON work_orders(alert_id);

-- =============================================
-- SEED DATA
-- =============================================

-- Insert Sites
INSERT INTO sites (code, name, address) VALUES
    ('CAS-S1', 'Tour Alpha - Casanearshore', 'Casanearshore Park, Batiment A, Casablanca'),
    ('CAS-S2', 'Tour Beta - Casanearshore', 'Casanearshore Park, Batiment B, Casablanca');

-- Insert Assets for Site 1 (CAS-S1)
INSERT INTO assets (code, type, site_id, status) VALUES
    ('CAS-S1-HVAC_1', 'HVAC', 1, 'OK'),
    ('CAS-S1-CHILLER_1', 'CHILLER', 1, 'OK'),
    ('CAS-S1-ELEVATOR_1', 'ELEVATOR', 1, 'OK');

-- Insert Assets for Site 2 (CAS-S2)
INSERT INTO assets (code, type, site_id, status) VALUES
    ('CAS-S2-HVAC_1', 'HVAC', 2, 'OK'),
    ('CAS-S2-CHILLER_1', 'CHILLER', 2, 'OK'),
    ('CAS-S2-ELEVATOR_1', 'ELEVATOR', 2, 'OK');

-- Insert Maintenance Policies (from PRD)

-- R1: HVAC - Performance clim degradee
INSERT INTO maintenance_policies (asset_type, metric, rule_type, threshold, condition, window_minutes, severity, description) VALUES
    ('HVAC', 'temp_supply_air', 'threshold', 20.0, '>', 15, 'MEDIUM', 'Performance clim degradee - temperature soufflage elevee');

-- R2: HVAC - Risque mecanique ventilateur
INSERT INTO maintenance_policies (asset_type, metric, rule_type, threshold, condition, window_minutes, severity, description) VALUES
    ('HVAC', 'vibration_level', 'threshold', 7.0, '>', 5, 'HIGH', 'Risque mecanique ventilateur - vibrations anormales');

-- R3: CHILLER - Refroidissement insuffisant
INSERT INTO maintenance_policies (asset_type, metric, rule_type, threshold, condition, window_minutes, severity, description) VALUES
    ('CHILLER', 'water_temp_out', 'threshold', 14.0, '>', 10, 'HIGH', 'Refroidissement insuffisant - eau glacee trop chaude');

-- R4: CHILLER - Maintenance preventive
INSERT INTO maintenance_policies (asset_type, metric, rule_type, threshold, condition, window_minutes, severity, description) VALUES
    ('CHILLER', 'run_hours', 'runtime', 500.0, '>', NULL, 'LOW', 'Maintenance preventive due - heures de fonctionnement');

-- R5: ELEVATOR - Surchauffe moteur
INSERT INTO maintenance_policies (asset_type, metric, rule_type, threshold, condition, window_minutes, severity, description) VALUES
    ('ELEVATOR', 'motor_temp', 'threshold', 80.0, '>', 5, 'HIGH', 'Surchauffe moteur ascenseur - arret immediat recommande');

-- R6: ELEVATOR - Usure portes
INSERT INTO maintenance_policies (asset_type, metric, rule_type, threshold, condition, window_minutes, severity, description) VALUES
    ('ELEVATOR', 'door_cycles', 'runtime', 100000.0, '>', NULL, 'MEDIUM', 'Inspection portes a planifier - cycles eleves');

-- =============================================
-- VIEWS for reporting
-- =============================================

-- View: Site status summary
CREATE VIEW site_status_summary AS
SELECT 
    s.id,
    s.code,
    s.name,
    COUNT(DISTINCT a.id) as total_assets,
    COUNT(DISTINCT CASE WHEN al.status = 'open' AND al.severity = 'HIGH' THEN al.id END) as high_alerts,
    COUNT(DISTINCT CASE WHEN al.status = 'open' AND al.severity = 'MEDIUM' THEN al.id END) as medium_alerts,
    COUNT(DISTINCT CASE WHEN al.status = 'open' AND al.severity = 'LOW' THEN al.id END) as low_alerts,
    COUNT(DISTINCT CASE WHEN wo.status IN ('open', 'in_progress') THEN wo.id END) as open_work_orders
FROM sites s
LEFT JOIN assets a ON a.site_id = s.id
LEFT JOIN alerts al ON al.asset_id = a.id
LEFT JOIN work_orders wo ON wo.alert_id = al.id
GROUP BY s.id, s.code, s.name;

-- View: Asset status with latest metrics info
CREATE VIEW asset_status_view AS
SELECT 
    a.id,
    a.code,
    a.type,
    a.status,
    s.code as site_code,
    s.name as site_name,
    COUNT(CASE WHEN al.status = 'open' THEN 1 END) as open_alerts
FROM assets a
JOIN sites s ON a.site_id = s.id
LEFT JOIN alerts al ON al.asset_id = a.id
GROUP BY a.id, a.code, a.type, a.status, s.code, s.name;
