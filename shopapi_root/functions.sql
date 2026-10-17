DELIMITER //

-- Список товаров с категорией
CREATE PROCEDURE sp_products_list ()
BEGIN
    SELECT p.product_id, p.name, c.name AS category, p.price, p.stock
      FROM products p
      JOIN categories c ON c.category_id = p.category_id
     ORDER BY p.name;
END //

-- Добавить товар
CREATE PROCEDURE sp_product_add (
    IN p_name VARCHAR(100),
    IN p_category_id INT,
    IN p_price DECIMAL(10,2),
    IN p_stock INT,
    OUT p_new_id INT
)
BEGIN
    INSERT INTO products (name, category_id, price, stock)
    VALUES (p_name, p_category_id, p_price, p_stock);
    SET p_new_id = LAST_INSERT_ID();
END //

-- Обновить цену товара
CREATE PROCEDURE sp_product_update_price (
    IN p_product_id INT,
    IN p_new_price DECIMAL(10,2)
)
BEGIN
    UPDATE products SET price = p_new_price WHERE product_id = p_product_id;
END //

-- Создать заказ
CREATE PROCEDURE sp_order_create (
    IN p_customer_id INT,
    OUT p_order_id INT
)
BEGIN
    INSERT INTO orders (customer_id, created_at, total)
    VALUES (p_customer_id, NOW(), 0);
    SET p_order_id = LAST_INSERT_ID();
END //

-- Добавить позицию в заказ (с проверкой остатка)
CREATE PROCEDURE sp_order_add_item (
    IN p_order_id INT,
    IN p_product_id INT,
    IN p_quantity INT,
    OUT p_success TINYINT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_stock INT;
    DECLARE v_price DECIMAL(10,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_success = 0;
        SET p_message = 'Ошибка при добавлении позиции';
        ROLLBACK;
    END;

    START TRANSACTION;

    SELECT stock, price INTO v_stock, v_price
      FROM products WHERE product_id = p_product_id FOR UPDATE;

    IF v_stock IS NULL THEN
        SET p_success = 0;
        SET p_message = 'Товар не найден';
        ROLLBACK;
    ELSEIF v_stock < p_quantity THEN
        SET p_success = 0;
        SET p_message = CONCAT('Недостаточно товара. Доступно: ', v_stock);
        ROLLBACK;
    ELSE
        INSERT INTO order_items (order_id, product_id, quantity, price)
        VALUES (p_order_id, p_product_id, p_quantity, v_price);

        UPDATE products SET stock = stock - p_quantity
         WHERE product_id = p_product_id;

        UPDATE orders o
           SET total = (SELECT SUM(quantity * price)
                          FROM order_items WHERE order_id = p_order_id)
         WHERE o.order_id = p_order_id;

        SET p_success = 1;
        SET p_message = 'OK';
        COMMIT;
    END IF;
END //

-- Все заказы клиента
CREATE PROCEDURE sp_customer_orders (IN p_customer_id INT)
BEGIN
    SELECT o.order_id, o.created_at, o.total,
           fn_customer_avg_check(o.customer_id) AS avg_check
      FROM orders o
     WHERE o.customer_id = p_customer_id
     ORDER BY o.created_at DESC;
END //

-- Статистика по категориям
CREATE PROCEDURE sp_category_stats ()
BEGIN
    SELECT c.name AS category,
           COUNT(DISTINCT p.product_id) AS products_count,
           IFNULL(SUM(oi.quantity), 0)  AS sold_units,
           IFNULL(SUM(oi.quantity * oi.price), 0) AS revenue
      FROM categories c
      LEFT JOIN products    p  ON p.category_id = c.category_id
      LEFT JOIN order_items oi ON oi.product_id = p.product_id
     GROUP BY c.category_id, c.name
     ORDER BY revenue DESC;
END //

DELIMITER ;
