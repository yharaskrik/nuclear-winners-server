from . import get_db

get_shipping_sql = "SELECT * FROM ShippingMethod"
get_shipping_sql_weight = "SELECT * FROM ShippingMethod WHERE maxWeight > %s"


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
