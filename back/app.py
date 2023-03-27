import os
from time import sleep

from flask import Flask, jsonify, request, g
from flasgger import Swagger
import psycopg2
from flask_cors import CORS, cross_origin
import connection

import db

app = Flask(__name__)


def create_schema():
    with app.app_context():
        cur = connection.conn.cursor()
    with open("create_schema.sql", "r") as scheme_f:
        cur.execute(scheme_f.read())
    connection.conn.commit()
    cur.close()


@app.route('/admin/add_company', methods=['POST'])
@cross_origin()
def add_company():
    data = request.get_json()
    company_id = db.add_company(connection.conn, data['company_name'])
    db.init_company_stocks(connection.conn, company_id, data['init_stock_price'], data['init_stock_quantity'])
    return jsonify({"company_id": str(company_id)})


@app.route('/admin/add_user', methods=['POST'])
@cross_origin()
def add_user():
    data = request.get_json()
    user_id = db.add_user(connection.conn, data['user_name'])
    db.init_user_balance(connection.conn, user_id)
    return jsonify({"user_id": str(user_id)})


@app.route('/admin/alter_stock_quantity', methods=['POST'])
@cross_origin()
def alter_stock_quantity():
    data = request.get_json()
    new_quantity = db.alter_company_stocks_quantity(connection.conn, data['company_id'], data['difference'])
    return jsonify({"company_id": data['company_id'], "stock_quantity": new_quantity})


@app.route('/admin/alter_stock_price', methods=['POST'])
@cross_origin()
def alter_stock_price():
    data = request.get_json()
    db.alter_company_stocks_price(connection.conn, data['company_id'], data['new_price'])
    return jsonify({})


@app.route('/get_user_summary', methods=['GET'])
@cross_origin()
def get_user_summary():
    user_id = request.args.get('user_id')
    user_name = db.get_user_name(connection.conn, user_id)
    if user_name is None:
        return {}, 404
    return jsonify({"user_name": user_name, "stocks": db.get_user_stocks_summary(connection.conn, user_id),
                    "balance": float(db.get_user_balance(connection.conn, user_id))})


@app.route('/get_companies_summary', methods=['GET'])
@cross_origin()
def get_companies_stock_summary():
    return jsonify({"stocks": db.get_companies_stock_summary(connection.conn)})


@app.route('/top_up_user_balance', methods=['POST'])
@cross_origin()
def top_up_balance():
    data = request.get_json()
    new_balance = db.top_up_user_balance(connection.conn, data['user_id'], data['amount'])
    return jsonify({"user_id": data['user_id'], "new_balance": float(new_balance)})


@app.route('/buy_stocks', methods=['POST'])
@cross_origin()
def buy_stocks():
    data = request.get_json()
    requested_quantity = data['quantity']
    user_id = data['user_id']
    company_id = data['company_id']

    user_balance = db.get_user_balance(connection.conn, user_id)
    if user_balance is None:
        return {"error_message": "No such user with given id"}, 404

    stock_quantity, stock_price = db.get_company_stock_info(connection.conn, company_id)
    if stock_quantity is None or stock_price is None:
        return {"error_message": "No such company with given id"}, 404

    if requested_quantity > stock_quantity:
        return jsonify({'transaction_status': 'FAILURE',
                        'message': f'Company does not have that much stocks: {requested_quantity} > {stock_quantity}'})

    total_stock_price = stock_price * requested_quantity
    if total_stock_price > user_balance:
        return jsonify({'transaction_status': 'FAILURE',
                        'message': f'Insufficient funds: {total_stock_price} > {user_balance}'})

    db.top_up_user_balance(connection.conn, user_id, -total_stock_price)
    db.add_user_stock_info(connection.conn, user_id, company_id, requested_quantity)
    db.alter_company_stocks_quantity(connection.conn, company_id, -requested_quantity)

    return jsonify(({'status': 'SUCCESS', 'message': 'OK'}))


@app.route('/sell_stocks', methods=['POST'])
@cross_origin()
def sell_stocks():
    data = request.get_json()
    requested_quantity = data['quantity']
    user_id = data['user_id']
    company_id = data['company_id']

    user_balance = db.get_user_balance(connection.conn, user_id)
    if user_balance is None:
        return {"error_message": "No such user with given id"}, 404

    company_stock_quantity, company_stock_price = db.get_company_stock_info(connection.conn, company_id)
    if company_stock_quantity is None or company_stock_price is None:
        return {"error_message": "No such company with given id"}, 404

    stock_quantity, stock_price = db.get_user_stock_info(connection.conn, user_id, company_id)

    if requested_quantity > stock_quantity:
        return jsonify({'status': 'FAILURE',
                        'message': f'User does not have that much stocks: {requested_quantity} > {stock_quantity}'})

    total_stock_price = stock_price * requested_quantity
    db.top_up_user_balance(connection.conn, user_id, total_stock_price)
    db.add_user_stock_info(connection.conn, user_id, company_id, -requested_quantity)
    db.alter_company_stocks_quantity(connection.conn, company_id, requested_quantity)

    return jsonify(({'status': 'SUCCESS', 'message': 'OK'}))


if __name__ == "__main__":
    sleep(1)  # wait for psql init
    connection.init()

    connection.conn = psycopg2.connect(
        host=os.environ['POSTGRES_HOST'],
        port=5432,
        database="stocks_db",
        user=os.environ['POSTGRES_USER']
    )
    create_schema()

    swagger = Swagger(app, template_file="api.yaml", config={"openapi": "3.0.0"}, merge=True)
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    app.run(port=8000, host='0.0.0.0')
