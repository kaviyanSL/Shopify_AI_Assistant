CREATE TABLE product_variant_ids (
    id BIGINT ,
    product_variant_ids JSON NOT NULL,  
    insert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);