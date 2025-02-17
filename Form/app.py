from flask import Flask, render_template, request
from datetime import datetime
import pyodbc

app = Flask(__name__)

# SQL Server connection
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=LAPTOP-82AUC5I5\SQLEXPRESS;'
        'DATABASE=CompanyDB;'
        'Trusted_Connection=yes;'
    )
    return conn

# Calculate age based on DOB
def calculate_age(dob):
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # Retrieve form data
        name = request.form['name']
        surname = request.form['surname']
        dob = request.form['dob']
        dob_dt = datetime.strptime(dob, '%Y-%m-%d')  # Convert string to date
        age = calculate_age(dob_dt)
        address = request.form['address']
        current_company = request.form['current_company']
        experience = request.form['experience']
        institute = request.form['institute']

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert data into the table
        insert_query = """
        INSERT INTO form (Name, Surname, DOB, Age, Address, CurrentCompany, Experience, Institute)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (name, surname, dob, age, address, current_company, experience, institute))

        # Commit and close the connection
        conn.commit()
        cursor.close()
        conn.close()

        # Send data back to the template
        return render_template('result.html', name=name, surname=surname, age=age,
                               address=address, current_company=current_company,
                               experience=experience, institute=institute)

    return render_template('form.html')

if __name__ == "__main__":
    app.run(debug=True)
