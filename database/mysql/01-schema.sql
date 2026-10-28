SET NAMES utf8mb4;

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL
) COMMENT = 'Categorias do catálogo de produtos';

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(120) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL COMMENT 'Preço de tabela atual em BRL',
    FOREIGN KEY (category_id) REFERENCES categories(id)
) COMMENT = 'Produtos vendidos pela loja';

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    state CHAR(2) NOT NULL COMMENT 'UF do cliente (ex.: SP, RJ)',
    created_at DATE NOT NULL COMMENT 'Data de cadastro do cliente'
) COMMENT = 'Clientes cadastrados';

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    status VARCHAR(20) NOT NULL COMMENT 'Status do pedido: paid, shipped, delivered ou cancelled. Em métricas de receita, exclua cancelled por padrão; contagens de pedidos incluem todos os status. Se o usuário pedir explicitamente todos os pedidos, inclua cancelled também na receita',
    ordered_at DATETIME NOT NULL COMMENT 'Data e hora em que o pedido foi feito',
    FOREIGN KEY (customer_id) REFERENCES customers(id)
) COMMENT = 'Pedidos realizados pelos clientes';

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL COMMENT 'Preço unitário praticado no momento da venda em BRL',
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
) COMMENT = 'Itens de cada pedido; receita = quantity * unit_price';
