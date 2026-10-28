CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INT NOT NULL REFERENCES categories(id),
    name VARCHAR(120) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    state CHAR(2) NOT NULL,
    created_at DATE NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    status VARCHAR(20) NOT NULL,
    ordered_at TIMESTAMP NOT NULL
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

COMMENT ON TABLE categories IS 'Categorias do catálogo de produtos';
COMMENT ON TABLE products IS 'Produtos vendidos pela loja';
COMMENT ON TABLE customers IS 'Clientes cadastrados';
COMMENT ON TABLE orders IS 'Pedidos realizados pelos clientes';
COMMENT ON TABLE order_items IS 'Itens de cada pedido; receita = quantity * unit_price';
COMMENT ON COLUMN products.unit_price IS 'Preço de tabela atual em BRL';
COMMENT ON COLUMN customers.state IS 'UF do cliente (ex.: SP, RJ)';
COMMENT ON COLUMN customers.created_at IS 'Data de cadastro do cliente';
COMMENT ON COLUMN orders.status IS 'Status do pedido: paid, shipped, delivered ou cancelled. Em métricas de receita, exclua cancelled por padrão; contagens de pedidos incluem todos os status. Se o usuário pedir explicitamente todos os pedidos, inclua cancelled também na receita';
COMMENT ON COLUMN orders.ordered_at IS 'Data e hora em que o pedido foi feito';
COMMENT ON COLUMN order_items.unit_price IS 'Preço unitário praticado no momento da venda em BRL';
