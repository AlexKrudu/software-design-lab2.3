CREATE USER test_user WITH PASSWORD 'test_password';
CREATE DATABASE stocks_db;
GRANT ALL PRIVILEGES ON DATABASE stocks_db TO test_user;