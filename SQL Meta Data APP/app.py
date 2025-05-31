from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlalchemy as sa
from sqlalchemy import create_engine
import pyodbc

app = Flask(__name__)
CORS(app)

# Replace with your server name
SERVER_NAME = 'LAPTOP-82AUC5I5\\SQLEXPRESS'

def get_connection(database=None):
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER_NAME};"
        f"{f'DATABASE={database};' if database else ''}"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/databases')
def get_databases():
    conn = get_connection('master')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master','tempdb','model','msdb')")
    databases = [row.name for row in cursor.fetchall()]
    conn.close()
    return jsonify(databases)

@app.route('/tables')
def get_tables():
    database = request.args.get('database')
    conn = get_connection(database)
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(tables)

@app.route('/columns')
def get_columns():
    database = request.args.get('database')
    table = request.args.get('table')
    conn = get_connection(database)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
    """, table)
    columns = [{
        'name': row.COLUMN_NAME,
        'type': row.DATA_TYPE,
        'nullable': row.IS_NULLABLE == 'YES'
    } for row in cursor.fetchall()]
    conn.close()
    return jsonify(columns)

@app.route('/stats')
def get_stats():
    database = request.args.get('database')
    table = request.args.get('table')
    conn = get_connection(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    row_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", table)
    col_count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'rows': row_count, 'columns': col_count})

@app.route('/views')
def get_views():
    database = request.args.get('database')
    conn = get_connection(database)
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS")
    views = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(views)

@app.route('/stored_procedures')
def get_stored_procedures():
    database = request.args.get('database')
    conn = get_connection(database)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name 
        FROM sys.objects 
        WHERE type = 'P' AND is_ms_shipped = 0
    """)
    procedures = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(procedures)

@app.route('/procedure_definition')
def get_procedure_definition():
    database = request.args.get('database')
    procedure_name = request.args.get('procedure')
    conn = get_connection(database)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sm.definition 
        FROM sys.sql_modules sm 
        JOIN sys.objects o ON sm.object_id = o.object_id 
        WHERE o.name = ?
    """, procedure_name)
    definition = cursor.fetchone()
    conn.close()
    return jsonify({'definition': definition[0] if definition else 'Not Found'})

@app.route('/sample_data')
def get_sample_data():
    database = request.args.get('database')
    table = request.args.get('table')
    limit = request.args.get('limit', 10)

    conn = get_connection(database)
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT TOP {limit} * FROM [{table}]")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        return jsonify({'columns': columns, 'rows': data})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()



if __name__ == '__main__':
    app.run(debug=True)
