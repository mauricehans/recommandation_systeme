-- Création de la table pour stocker les recommandations précalculées
CREATE TABLE IF NOT EXISTS product_recommendations (
    source_item_id INT,
    recommended_item_id INT,
    score INT,
    recommendation_type VARCHAR(50),
    last_updated DATETIME,
    PRIMARY KEY (source_item_id, recommended_item_id, recommendation_type)
);

-- Procédure pour mettre à jour les recommandations BOUGHT_TOGETHER
DELIMITER //
CREATE PROCEDURE update_bought_together_recommendations()
BEGIN
    INSERT INTO product_recommendations
    SELECT 
        p1.item_id as source_item_id,
        p2.item_id as recommended_item_id,
        COUNT(*) as score,
        'BOUGHT_TOGETHER' as recommendation_type,
        NOW() as last_updated
    FROM purchases p1
    JOIN purchases p2 ON p1.session_id = p2.session_id
    WHERE p1.item_id <> p2.item_id
    AND p1.purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY p1.item_id, p2.item_id
    ON DUPLICATE KEY UPDATE 
        score = VALUES(score),
        last_updated = VALUES(last_updated);
END //
DELIMITER ;

-- Procédure pour mettre à jour les recommandations VIEW_TO_PURCHASE
DELIMITER //
CREATE PROCEDURE update_view_to_purchase_recommendations()
BEGIN
    INSERT INTO product_recommendations
    SELECT 
        s.item_id as source_item_id,
        p.item_id as recommended_item_id,
        COUNT(*) as score,
        'VIEW_TO_PURCHASE' as recommendation_type,
        NOW() as last_updated
    FROM sessions s
    JOIN purchases p ON s.session_id = p.session_id
    WHERE s.item_id <> p.item_id
    AND s.view_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY s.item_id, p.item_id
    ON DUPLICATE KEY UPDATE 
        score = VALUES(score),
        last_updated = VALUES(last_updated);
END //
DELIMITER ;

-- Événement pour mettre à jour automatiquement les recommandations chaque jour
CREATE EVENT IF NOT EXISTS update_recommendations
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    CALL update_bought_together_recommendations();
    CALL update_view_to_purchase_recommendations();
END;