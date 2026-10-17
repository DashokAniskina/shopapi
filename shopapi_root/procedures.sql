DELIMITER //

-- Средний чек клиента
CREATE FUNCTION fn_customer_avg_check (p_customer_id INT)
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
    DECLARE v_avg DECIMAL(12,2);
    SELECT IFNULL(AVG(total), 0) INTO v_avg
      FROM orders WHERE customer_id = p_customer_id;
    RETURN v_avg;
END //

-- Доступное количество товара
CREATE FUNCTION fn_product_available (p_product_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_stock INT;
    SELECT stock INTO v_stock FROM products WHERE product_id = p_product_id;
    RETURN IFNULL(v_stock, 0);
END //

-- Скидка для клиента по возрасту и сумме
CREATE FUNCTION fn_customer_discount (p_customer_id INT, p_amount DECIMAL(12,2))
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_age INT;
    DECLARE v_discount DECIMAL(5,2) DEFAULT 0;

    SELECT age INTO v_age FROM customers WHERE customer_id = p_customer_id;

    IF v_age < 18 THEN SET v_discount = 0;
    ELSEIF v_age >= 60 THEN SET v_discount = 10;
    ELSEIF p_amount >= 10000 THEN SET v_discount = 7;
    ELSE SET v_discount = 3;
    END IF;

    RETURN v_discount;
END //

DELIMITER ;
