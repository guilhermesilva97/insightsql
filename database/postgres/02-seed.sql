INSERT INTO categories (name) VALUES
    ('Eletrônicos'), ('Livros'), ('Casa'), ('Esporte'), ('Moda');

INSERT INTO products (category_id, name, unit_price) VALUES
    (1, 'Notebook Pro 14', 6499.00),
    (1, 'Fone Bluetooth', 349.90),
    (1, 'Monitor 27 4K', 2199.00),
    (2, 'Arquitetura Limpa', 89.90),
    (2, 'Domain-Driven Design', 129.00),
    (2, 'O Programador Pragmático', 99.90),
    (3, 'Cafeteira Elétrica', 279.00),
    (3, 'Aspirador Robô', 1599.00),
    (3, 'Jogo de Panelas', 459.00),
    (4, 'Bicicleta Aro 29', 2399.00),
    (4, 'Tênis de Corrida', 499.90),
    (4, 'Kit Halteres', 319.00),
    (5, 'Jaqueta Jeans', 259.90),
    (5, 'Mochila Executiva', 389.00),
    (5, 'Relógio Casual', 599.00);

INSERT INTO customers (name, state, created_at)
SELECT
    (ARRAY['Ana', 'Bruno', 'Carla', 'Diego', 'Elisa', 'Felipe', 'Gabriela', 'Henrique', 'Isabela', 'João', 'Larissa', 'Marcos'])[1 + g % 12]
        || ' '
        || (ARRAY['Silva', 'Souza', 'Oliveira', 'Santos', 'Pereira', 'Costa', 'Rodrigues', 'Almeida', 'Lima', 'Carvalho'])[1 + (g / 12) % 10],
    (ARRAY['SP', 'RJ', 'MG', 'PR', 'SC', 'RS', 'BA', 'PE', 'GO', 'DF'])[1 + (g * 3) % 10],
    DATE '2023-01-01' + (g * 7) % 600
FROM generate_series(1, 300) AS g;

INSERT INTO orders (customer_id, status, ordered_at)
SELECT
    1 + (g * 37) % 300,
    (ARRAY['paid', 'paid', 'paid', 'shipped', 'delivered', 'delivered', 'cancelled'])[1 + g % 7],
    TIMESTAMP '2024-01-01' + make_interval(days => (g * 13) % 640, hours => g % 24)
FROM generate_series(1, 3000) AS g;

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT o.id, p.id, 1 + (o.id + p.id) % 3, p.unit_price
FROM orders AS o
JOIN products AS p ON (o.id + p.id * 7) % 11 = 0;
