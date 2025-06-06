from flask import Flask, render_template, request, redirect, url_for, g, Response
import sqlite3
import csv
from io import StringIO
from datetime import date

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    db = get_db()
    employees = db.execute("SELECT * FROM employees").fetchall()
    return render_template("index.html", employees=employees)

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    db = get_db()
    today = str(date.today())
    for emp_id in request.form:
        status = request.form[emp_id]
        db.execute("INSERT INTO attendance (emp_id, date, status) VALUES (?, ?, ?)", (emp_id, today, status))
    db.commit()
    return redirect(url_for("index"))

@app.route("/edit_salary/<int:emp_id>", methods=["GET", "POST"])
def edit_salary(emp_id):
    db = get_db()
    if request.method == "POST":
        new_salary = request.form["salary"]
        db.execute("UPDATE employees SET salary = ? WHERE id = ?", (new_salary, emp_id))
        db.commit()
        return redirect(url_for("index"))
    employee = db.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
    return render_template("edit_salary.html", employee=employee)

@app.route("/dashboard")
def dashboard():
    db = get_db()
    rows = db.execute("""
        SELECT e.name,
               SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_count
        FROM employees e
        LEFT JOIN attendance a ON e.id = a.emp_id
        GROUP BY e.id
    """).fetchall()
    names = [row["name"] for row in rows]
    presents = [row["present_count"] or 0 for row in rows]
    absents = [row["absent_count"] or 0 for row in rows]
    return render_template("dashboard.html", names=names, presents=presents, absents=absents)

@app.route("/export_dashboard")
def export_dashboard():
    db = get_db()
    rows = db.execute("""
        SELECT e.name,
               SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_count
        FROM employees e
        LEFT JOIN attendance a ON e.id = a.emp_id
        GROUP BY e.id
    """).fetchall()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Employee Name", "Days Present", "Days Absent"])
    for row in rows:
        cw.writerow([row["name"], row["present_count"] or 0, row["absent_count"] or 0])
    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=attendance_report.csv"})

if __name__ == "__main__":
    app.run(debug=True)
