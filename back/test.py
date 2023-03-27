import unittest
import testcontainers.postgres
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app import app
import connection


def cleanup(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM company_stocks WHERE true")
    cur.execute("DELETE FROM user_stocks WHERE true")
    cur.execute("DELETE FROM user_balance WHERE true")
    cur.execute("DELETE FROM users WHERE true")
    cur.execute("DELETE FROM companies WHERE true")
    conn.commit()
    cur.close()


class TestApp(unittest.TestCase):
    conn = None
    postgres = None

    @classmethod
    def setUpClass(cls):
        cls.postgres = testcontainers.postgres.PostgresContainer()
        cls.postgres.start()
        test_db_name = "test_stock_db"
        init_con = psycopg2.connect(dbname='postgres',
                                    host=cls.postgres.get_container_host_ip(),
                                    port=cls.postgres.get_exposed_port(5432),
                                    user="test",
                                    password="test"
                                    )
        init_con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        init_cur = init_con.cursor()
        init_cur.execute(
            f"CREATE DATABASE {test_db_name};"
        )
        init_con.close()
        connection.init()

        connection.conn = psycopg2.connect(
            host=cls.postgres.get_container_host_ip(),
            port=cls.postgres.get_exposed_port(5432),
            database=test_db_name,
            user="test",
            password="test"
        )

        with app.app_context():
            cur = connection.conn.cursor()
            with open("create_schema.sql", "r") as scheme_f:
                cur.execute(scheme_f.read())
            connection.conn.commit()
            cur.close()

    @classmethod
    def tearDownClass(cls):
        connection.conn.close()
        cls.postgres.stop()

    def setUp(self):
        self.addCleanup(cleanup, connection.conn)
        self.app = app.test_client()

    def test_add_user(self):
        test_username = "test_username"
        create_user_response = self.app.post('/admin/add_user', json={"user_name": test_username})
        user_id = create_user_response.json['user_id']

        user_summary_response = self.app.get('/get_user_summary', query_string={"user_id": user_id})

        self.assertEqual(user_summary_response.json, {'balance': 0.0, 'stocks': [], 'user_name': test_username})

    def test_init_company(self):
        test_company_name = "test_company_name"
        init_stock_price = 1.22
        init_stock_quantity = 100
        init_company_response = self.app.post('/admin/add_company', json={"company_name": test_company_name,
                                                                          "init_stock_price": init_stock_price,
                                                                          "init_stock_quantity": init_stock_quantity})
        company_id = init_company_response.json['company_id']

        companies_summary_response = self.app.get('/get_companies_summary')
        self.assertEqual(companies_summary_response.json, {'stocks': [
            {'company_id': int(company_id), 'company_name': test_company_name, 'quantity': init_stock_quantity,
             'stock_price': init_stock_price}]})

    def test_buy_stocks_insufficient_funds(self):
        test_username = "test_username"
        create_user_response = self.app.post('/admin/add_user', json={"user_name": test_username})
        user_id = create_user_response.json['user_id']

        test_company_name = "test_company_name"
        init_stock_price = 1.22
        init_stock_quantity = 100
        init_company_response = self.app.post('/admin/add_company', json={"company_name": test_company_name,
                                                                          "init_stock_price": init_stock_price,
                                                                          "init_stock_quantity": init_stock_quantity})
        company_id = init_company_response.json['company_id']

        buy_stocks_response = self.app.post('/buy_stocks',
                                            json={"user_id": user_id, "company_id": company_id, "quantity": 1})
        self.assertEqual(buy_stocks_response.json,
                         {'message': f'Insufficient funds: {init_stock_price} > 0.00', 'transaction_status': 'FAILURE'})

    def test_buy_stocks_success(self):
        test_username = "test_username"
        create_user_response = self.app.post('/admin/add_user', json={"user_name": test_username})
        user_id = create_user_response.json['user_id']
        quantity_to_buy = 1
        user_balance = 100

        test_company_name = "test_company_name"
        init_stock_price = 2
        init_stock_quantity = 100
        init_company_response = self.app.post('/admin/add_company', json={"company_name": test_company_name,
                                                                          "init_stock_price": init_stock_price,
                                                                          "init_stock_quantity": init_stock_quantity})
        company_id = init_company_response.json['company_id']
        self.app.post('/top_up_user_balance', json={"user_id": user_id, "amount": user_balance})
        buy_stocks_response = self.app.post('/buy_stocks',
                                            json={"user_id": user_id, "company_id": company_id, "quantity": 1})
        self.assertEqual(buy_stocks_response.json, {'message': 'OK', 'status': 'SUCCESS'})

        user_summary_response = self.app.get('/get_user_summary', query_string={"user_id": user_id})
        self.assertEqual(user_summary_response.json,
                         {'balance': float(user_balance - init_stock_price * quantity_to_buy), 'stocks': [
                             {'company_id': int(company_id), 'company_name': test_company_name,
                              'quantity': quantity_to_buy,
                              'stock_price': float(init_stock_price)}],
                          'user_name': test_username})
