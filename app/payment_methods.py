from . import get_db

get_payment_methods_sql = "SELECT * FROM PaymentMethod"


def get_payment_methods():
    """Gets all the payment methods from the database.

    :returns A list of dicts with the keys of methodID and name"""
    with get_db().cursor() as cursor:
        cursor.execute(get_payment_methods_sql)
        return cursor.fetchall()
