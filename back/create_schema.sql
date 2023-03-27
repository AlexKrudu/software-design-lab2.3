CREATE TABLE IF NOT EXISTS companies
(
    company_id   SERIAL PRIMARY KEY,
    company_name TEXT
);

CREATE TABLE IF NOT EXISTS company_stocks
(
    company_id SERIAL PRIMARY KEY REFERENCES companies (company_id),
    price      NUMERIC(10, 2),
    quantity   INTEGER
);

CREATE TABLE IF NOT EXISTS users
(
    user_id   SERIAL PRIMARY KEY,
    user_name TEXT
);

CREATE TABLE IF NOT EXISTS user_stocks
(
    user_id    SERIAL REFERENCES users (user_id),
    company_id SERIAL REFERENCES companies (company_id),
    quantity   INTEGER,

    CONSTRAINT unique_user_company UNIQUE (user_id, company_id)
);

CREATE TABLE IF NOT EXISTS user_balance
(
    user_id SERIAL REFERENCES users (user_id),
    balance NUMERIC(10, 2)
)