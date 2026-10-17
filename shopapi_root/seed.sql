INSERT INTO categories (name) VALUES
('Электроника'), ('Книги'), ('Одежда');

INSERT INTO products (name, category_id, price, stock) VALUES
('Смартфон', 1, 29990.00, 15),
('Ноутбук', 1, 75990.00, 7),
('Роман «1984»', 2, 890.00, 40),
('Футболка', 3, 1500.00, 25);

INSERT INTO customers (first_name, last_name, email, age) VALUES
('Иван', 'Иванов', 'ivanov@example.com', 25),
('Анна', 'Петрова', 'petrova@example.com', 62),
('Пётр', 'Сидоров', 'sidorov@example.com', 17);
