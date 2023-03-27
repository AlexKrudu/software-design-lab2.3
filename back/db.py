

def add_user(connection, user_name):
    cur = connection.cursor()
    cur.execute(f"INSERT INTO users(user_name) VALUES ('{user_name}') RETURNING user_id")
    user_id = cur.fetchone()[0]
    cur.close()
    return user_id


def init_user_balance(connection, user_id):
    cur = connection.cursor()
    cur.execute(f"INSERT INTO user_balance(user_id, balance) VALUES ({user_id}, 0) RETURNING user_id")
    cur.close()


def get_user_name(connection, user_id):
    cur = connection.cursor()
    cur.execute(f"SELECT user_name FROM users WHERE user_id = {user_id}")
    user_name = cur.fetchone()
    cur.close()
    if user_name is None:
        return None
    return user_name[0]


def add_company(connection, company_name):
    cur = connection.cursor()
    cur.execute(f"INSERT INTO companies(company_name) VALUES ('{company_name}') RETURNING company_id")
    company_id = cur.fetchone()[0]
    cur.close()
    return company_id


def init_company_stocks(connection, company_id, init_price, init_quantity):
    cur = connection.cursor()
    cur.execute(
        f"INSERT INTO company_stocks(company_id, price, quantity) VALUES ({company_id}, {init_price}, {init_quantity})")
    cur.close()


def alter_company_stocks_price(connection, company_id, new_price):
    cur = connection.cursor()
    cur.execute(f"UPDATE company_stocks SET price = {new_price} WHERE company_id = {company_id}")
    cur.close()


def alter_company_stocks_quantity(connection, company_id, difference):
    cur = connection.cursor()
    cur.execute(
        f"UPDATE company_stocks SET quantity = quantity + {difference} WHERE company_id = {company_id} RETURNING quantity")
    new_quantity = cur.fetchone()[0]
    cur.close()
    return new_quantity


def add_user_stock_info(connection, user_id, company_id, difference):
    cur = connection.cursor()
    cur.execute(
        f"INSERT INTO user_stocks(user_id, company_id, quantity) VALUES ({user_id}, {company_id}, {difference}) "
        f"ON CONFLICT (user_id, company_id) DO UPDATE SET quantity = EXCLUDED.quantity + user_stocks.quantity RETURNING quantity")
    new_quantity = cur.fetchone()[0]
    cur.close()
    return new_quantity


def get_user_stocks_summary(connection, user_id):
    result = []
    cur = connection.cursor()
    cur.execute(
        f"SELECT user_stocks.company_id, company_name, company_stocks.price, user_stocks.quantity FROM"
        f" user_stocks INNER JOIN company_stocks on user_stocks.company_id = company_stocks.company_id"
        f" INNER JOIN companies ON user_stocks.company_id = companies.company_id WHERE user_id = {user_id}"
    )
    for row in cur:
        result.append(
            {'company_id': row[0], 'company_name': row[1], 'stock_price': float(row[2]), 'quantity': int(row[3])})
    cur.close()

    return result


def get_companies_stock_summary(connection):
    result = []
    cur = connection.cursor()
    cur.execute(
        "SELECT company_id, company_name, price, quantity FROM company_stocks NATURAL JOIN companies"
    )
    for row in cur:
        result.append(
            {'company_id': row[0], 'company_name': row[1], 'stock_price': float(row[2]), 'quantity': int(row[3])})
    cur.close()

    return result


def top_up_user_balance(connection, user_id, difference):
    cur = connection.cursor()
    cur.execute(
        f"UPDATE user_balance SET balance = balance + {difference} WHERE user_id = {user_id} RETURNING balance"
    )
    new_balance = cur.fetchone()[0]
    cur.close()

    return new_balance


def get_user_balance(connection, user_id):
    cur = connection.cursor()
    cur.execute(f"SELECT balance FROM user_balance WHERE user_id = {user_id}")
    balance = cur.fetchone()
    if balance is None:
        return None
    cur.close()

    return balance[0]


def get_user_stock_info(connection, user_id, company_id):
    cur = connection.cursor()
    cur.execute(
        f"SELECT company_stocks.price, user_stocks.quantity FROM"
        f" user_stocks INNER JOIN company_stocks ON user_stocks.company_id = company_stocks.company_id WHERE user_id = {user_id} AND user_stocks.company_id = {company_id}"
    )
    res = cur.fetchone()
    if res is None:
        return 0, None
    quantity, price = res[1], res[0]
    cur.close()

    return quantity, price


def get_company_stock_info(connection, company_id):
    cur = connection.cursor()
    cur.execute(
        f"SELECT price, quantity FROM"
        f" company_stocks WHERE company_id = {company_id}"
    )
    res = cur.fetchone()
    if res is None:
        return None, None

    quantity, price = res[1], res[0]
    cur.close()

    return quantity, price
