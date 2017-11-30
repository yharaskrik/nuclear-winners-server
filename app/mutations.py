from flask import current_app
from pymysql import Error

from . import get_db

get_mutations_sql = "SELECT name, id FROM Mutation"


def get_mutations():
    try:
        with get_db().cursor() as cursor:
            cursor.execute(get_mutations_sql)
            mutations = cursor.fetchall()
            return mutations
    except Error as e:
        current_app.logger.error(e)
        return list()


delete_mutations_sql = "DELETE FROM UserMutation WHERE userID = %s"


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
            cursor.execute(delete_mutations_sql)
            args = [(user_id, mid) for mid in mutations]
            cursor.executemany(
                "INSERT INTO UserMutation(mutationID, userID) VALUES (%s)" % ",".join(["%s"] * len(mutations)), args)
            get_db().commit()
            return True
    except Error as e:
        current_app.logger.error(e)
        return False
