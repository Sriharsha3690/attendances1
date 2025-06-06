
import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

# Database setup
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    salary REAL NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emp_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY(emp_id) REFERENCES employees(id))''')

    c.execute("SELECT COUNT(*) FROM employees")
    if c.fetchone()[0] == 0:
        employees = [
            ('Alice', 30000), ('Bob', 28000), ('Charlie', 32000),
            ('David', 31000), ('Eva', 29500), ('Frank', 27000),
            ('Grace', 33000), ('Hannah', 28500), ('Ian', 27500), ('Jane', 29000)
        ]
        c.executemany("INSERT INTO employees (name, salary) VALUES (?, ?)", employees)
        conn.commit()

def mark_attendance():
    st.subheader("Mark Attendance")
    today = str(date.today())
    employees = c.execute("SELECT * FROM employees").fetchall()

    attendance_data = {}
    for emp in employees:
        status = st.selectbox(f"{emp[1]} (ID {emp[0]})", ['present', 'absent'], key=emp[0])
        attendance_data[emp[0]] = status

    if st.button("Submit Attendance"):
        for emp_id, status in attendance_data.items():
            c.execute("INSERT INTO attendance (emp_id, date, status) VALUES (?, ?, ?)", (emp_id, today, status))
        conn.commit()
        st.success("Attendance marked successfully.")

def edit_salary():
    st.subheader("Edit Employee Salary")
    employees = c.execute("SELECT * FROM employees").fetchall()
    for emp in employees:
        new_salary = st.number_input(f"New salary for {emp[1]} (₹)", value=float(emp[2]), key=emp[0])
        if st.button(f"Update {emp[1]}", key=f"btn_{emp[0]}"):
            c.execute("UPDATE employees SET salary = ? WHERE id = ?", (new_salary, emp[0]))
            conn.commit()
            st.success(f"Updated salary for {emp[1]}")

def dashboard():
    st.subheader("Attendance Dashboard")
    data = c.execute("""
        SELECT e.name,
               SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present,
               SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent
        FROM employees e
        LEFT JOIN attendance a ON e.id = a.emp_id
        GROUP BY e.id
    """).fetchall()

    df = pd.DataFrame(data, columns=["Employee", "Days Present", "Days Absent"])
    st.dataframe(df)

    if st.button("Export CSV"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report", csv, "attendance_report.csv", "text/csv")

def main():
    st.title("🧾 PagarBook Clone – Attendance & Payroll")
    tabs = st.sidebar.radio("Navigate", ["📋 Mark Attendance", "💰 Edit Salary", "📊 Dashboard"])
    init_db()
    if tabs == "📋 Mark Attendance":
        mark_attendance()
    elif tabs == "💰 Edit Salary":
        edit_salary()
    elif tabs == "📊 Dashboard":
        dashboard()

if __name__ == '__main__':
    main()
