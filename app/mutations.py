from flask import current_app
from pymysql import Error

from . import get_db
from .util import get_user_id

get_mutations_sql = "SELECT name, id FROM Mutation"
get_user_mutations_sql = "SELECT Mutation.id FROM Mutation JOIN UserMutation ON Mutation.id = UserMutation.mutationID " \
                         "WHERE userID = %s"
delete_mutations_sql = "DELETE FROM UserMutation WHERE userID = %s"
sql = "INSERT INTO UserMutation(userID, mutationID) VALUES (%s, %s)"


def get_mutations():
    try:
        with get_db().cursor() as cursor:
            cursor.execute(get_mutations_sql)
            mutations = cursor.fetchall()
            return mutations
    except Error as e:
        current_app.logger.error(e)
        return list()


def get_user_mutations():
    """Returns a list of ids of mutations that the user has"""
    try:
        with get_db().cursor() as cursor:
            cursor.execute(get_user_mutations_sql, get_user_id())
            mutations = cursor.fetchall()

            return [m["id"] for m in mutations]
    except Error as e:
        current_app.logger.error(e)
        return list()


def set_mutations(user_id, mutations):
    """Sets the user to have some specific mutations.
    Note that this clears the existing mutations from the user before saving to the database.

    This calls commit on the database calls.

    :param user_id: The user id of the current user to update the mutations
    :param mutations: A list of the mutations
    :return: True if the update succeeded, False otherwise
    """
    try:
        with get_db().cursor() as cursor:
            cursor.execute(delete_mutations_sql, user_id)
            args = [(user_id, mid) for mid in mutations]
            cursor.executemany(sql, args)
            get_db().commit()
            return True
    except Error as e:
        current_app.logger.error("Mutations" + str(e) + " " + cursor._last_executed)
        return False
