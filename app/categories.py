from flask import render_template, request, redirect, flash, url_for

from app.user_login import requires_roles
from . import app, get_db
from .util import get_user_object


@app.route("/admin/categories")
@requires_roles("admin")
def manage_categories():
    """Displays the list of categories with the number of products in each category"""
    return render_template("manage_categories.html", categories=fetch_categories(), user=get_user_object())


@app.route("/admin/categories/add", methods=['GET', 'POST'])
@requires_roles("admin")
def add_category():
    """Adds a category to the database"""
    # Return the html for adding a category on a get request
    if request.method == 'GET':
        return render_template("add_edit_category.html", data={}, user=get_user_object())

    # Validates the name is not empty
    name = request.form['name']
    if not name:
        flash("Name cannot be empty", "error")
        # Reshow the form
        return render_template("add_edit_category.html", data=request.form, user=get_user_object())

    if insert_category(name):
        flash("Created category " + name, "success")
        return redirect(url_for("manage_categories"))
    else:
        # An error occurred
        flash("Unable to create category. Please try again", "error")
        return render_template("add_edit_category.html", data=request.form, user=get_user_object())


@app.route("/admin/categories/edit/<int:catID>", methods=['GET', 'POST'])
@requires_roles("admin")
def edit_category(catID):
    if request.method == 'GET':
        with get_db().cursor() as cursor:
            cursor.execute("SELECT id, name FROM Category WHERE id = %s", catID)
            data = cursor.fetchone()
        return render_template("add_edit_category.html", data=data, user=get_user_object())

    name = request.form['name']
    if not name:
        flash("Name cannot be empty", "error")
        return render_template("add_edit_category.html", data=request.form, user=get_user_object())

    if update_category(catID, name):
        flash("Updated category name to " + name, "success")
        return redirect(url_for("manage_categories"))
    flash("Could not update the category name. Please try again", "error")
    return render_template("add_edit_category.html", data=request.form, user=get_user_object())


@app.route("/browse/")
def view_categories():
    cat = fetch_categories()
    return render_template('list_categories.html', categories=cat, user=get_user_object())


@app.context_processor
def categories_list():
    return dict(catgories=fetch_categories())


def fetch_categories():
    """Fetched and returns all the categories from the database

    :returns a list of dicts containing categories. Each category contains: id, name, productCount
    """
    sql = "SELECT C.id, C.name, count(P.sku) AS productCount " \
          "FROM Category C LEFT OUTER JOIN Product P ON C.id = P.category " \
          "GROUP BY C.id"
    with get_db().cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def insert_category(name):
    """Inserts a category into the database.

    :returns True if the insert is successful. False if the insert fails."""
    sql = "INSERT INTO Category (name) VALUES (%s)"
    try:
        with get_db().cursor() as cursor:
            rows = cursor.execute(sql, name)
            get_db().commit()
            # Check if a row was created.
            return rows == 1
    except Exception as e:
        app.log_exception(e)
        return False


def update_category(cat_id, name):
    """Updates a category name in the database.

    :returns True if the update is successful. False if the update fails."""
    sql = "UPDATE Category SET name = %s WHERE id = %s"
    try:
        with get_db().cursor() as cursor:
            rows = cursor.execute(sql, (name, cat_id))
            get_db().commit()
            # Check if a row was affected.
            return rows == 1
    except Exception as e:
        app.log_exception(e)
        return False
