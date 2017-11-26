from . import get_db

get_shipping_sql = "SELECT * FROM ShippingMethod"
get_shipping_sql_weight = "SELECT * FROM ShippingMethod WHERE maxWeight > %s"
get_price_sql = "SELECT price FROM ShippingMethod WHERE methodID = %s"


def get_shipping_methods(weight=None):
    """Gets all the shipping methods valid for the passed in weight"""
    sql = get_shipping_sql
    args = []
    if weight is not None:
        sql = get_shipping_sql_weight
        args.append(weight)

    with get_db().cursor() as cursor:
        cursor.execute(sql, args)
        return cursor.fetchall()


def get_shipping_method_price(sid):
    """Gets and returns the price for a shipping methods

    :arg sid The shipping method id
    :returns The price in caps for this shipping method
    """
    with get_db().cursor() as cursor:
        cursor.execute(get_price_sql, sid)
        return cursor.fetchone()["price"]
