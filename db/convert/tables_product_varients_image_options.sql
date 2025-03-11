CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    vendor VARCHAR(100),
    handle VARCHAR(100) UNIQUE,
    tags VARCHAR(255),
    status ENUM('active', 'archived', 'draft') NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
) ;

CREATE TABLE variants (
    id BIGINT PRIMARY KEY,
    product_id BIGINT,
    title VARCHAR(255),
    price DECIMAL(10,2) NOT NULL,
    inventory_quantity INT NOT NULL,
    sku VARCHAR(50),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ;

CREATE TABLE options (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id BIGINT,
    name VARCHAR(100) NOT NULL,
    `values` TEXT NOT NULL, 
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ;

CREATE TABLE images (
    id BIGINT PRIMARY KEY,
    product_id BIGINT,
    src TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ;
