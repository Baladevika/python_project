"""
from flask import Flask, render_template, request
import pandas as pd
import pymysql
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MySQL config
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'sample'
}

table_name = 'your_table_name'  # Replace with your actual table name

# Get column headers from MySQL table
def get_mysql_headers():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return columns

@app.route('/')
def index():
    return render_template('upload.html', message=None)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return render_template('upload.html', message="No file selected.")

    file = request.files['file']
    if file.filename == '':
        return render_template('upload.html', message="No file selected.")

    if file and file.filename.lower().endswith(('.xls', '.xlsx')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            df = pd.read_excel(filepath).fillna('')
            excel_headers = df.columns.tolist()
            db_headers = get_mysql_headers()

            # Ensure 'upload_time' is not part of headers for comparison
            db_compare_headers = [col for col in db_headers if col != 'upload_time']

            if excel_headers != db_compare_headers:
                return render_template('upload.html', message="Header mismatch! Please upload a file with correct headers.")

            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            columns = ', '.join([f"`{col}`" for col in df.columns] + ['upload_time'])
            placeholders = ', '.join(['%s'] * len(df.columns) + ['%s'])
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            for _, row in df.iterrows():
                cursor.execute(sql, tuple(row) + (upload_time,))

            conn.commit()
            cursor.close()
            conn.close()

            return display_table()

        except Exception as e:
            return render_template('upload.html', message=f"Error: {e}")

    else:
        return render_template('upload.html', message="Invalid file type. Please upload .xls or .xlsx.")

@app.route('/update_table', methods=['GET', 'POST'])
def display_table():
    search_query = request.form.get('search', '').strip()
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    if search_query:
        sql = f"SELECT * FROM {table_name} WHERE CONCAT_WS(' ', {', '.join(get_mysql_headers())}) LIKE %s ORDER BY upload_time DESC"
        cursor.execute(sql, (f'%{search_query}%',))
    else:
        sql = f"SELECT * FROM {table_name} ORDER BY upload_time DESC"
        cursor.execute(sql)

    rows = cursor.fetchall()
    columns = get_mysql_headers()
    cursor.close()
    conn.close()

    # Group rows by upload_time
    grouped_data = {}
    upload_time_index = columns.index("upload_time")
    for row in rows:
        key = row[upload_time_index]
        grouped_data.setdefault(key, []).append(row)

    return render_template('update_table.html', columns=columns, grouped_data=grouped_data, search_query=search_query)

if __name__ == '__main__':
    app.run(debug=True)

"""
from flask import Flask, render_template, request
import pandas as pd
import pymysql
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import traceback

app1 = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app1.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'sample'
}

# Replace with your actual table name
table_name = 'your_table_name'


# Helper: Get column headers from the MySQL table
def get_mysql_headers():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return columns


# Route: Home
@app1.route('/')
def index():
    return render_template('upload.html', message=None)


# Route: Upload Excel and Insert to DB
@app1.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or request.files['file'].filename == '':
        return render_template('upload.html', message="No file selected.")

    file = request.files['file']
    if file and file.filename.lower().endswith(('.xls', '.xlsx')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app1.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            df = pd.read_excel(filepath).fillna('')
            excel_headers = df.columns.tolist()
            db_headers = get_mysql_headers()

            # Exclude upload_time from comparison
            db_compare_headers = [col for col in db_headers if col != 'upload_time']

            if excel_headers != db_compare_headers:
                return render_template('upload.html', message="Header mismatch! Please upload a file with correct headers.")

            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            columns = ', '.join([f"`{col}`" for col in df.columns] + ['upload_time'])
            placeholders = ', '.join(['%s'] * len(df.columns) + ['%s'])
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            for _, row in df.iterrows():
                cursor.execute(sql, tuple(row) + (upload_time,))

            conn.commit()
            cursor.close()
            conn.close()

            return render_template('upload.html', success_message="Upload successful!")

        except Exception as e:
            traceback.print_exc()
            return render_template('upload.html', message=f"Error: {e}")
    else:
        return render_template('upload.html', message="Invalid file type. Please upload .xls or .xlsx.")


# Route: Display or Search Table
@app1.route('/update_table', methods=['GET', 'POST'])
def display_table():
    search_query = request.values.get('search', '').strip()

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        all_columns = get_mysql_headers()
        columns = [col for col in all_columns if col != 'upload_time']

        if search_query:
            if ':' in search_query:
                col, val = map(str.strip, search_query.split(':', 1))
                if col in columns:
                    sql = f"SELECT * FROM {table_name} WHERE LOWER(`{col}`) LIKE %s ORDER BY upload_time DESC"
                    cursor.execute(sql, (f"%{val.lower()}%",))
                else:
                    return render_template('update_table.html', columns=columns, grouped_data={}, search_query=search_query, message="Invalid column name.")
            else:
                like_clause = " OR ".join([f"LOWER(`{col}`) LIKE %s" for col in columns])
                sql = f"SELECT * FROM {table_name} WHERE {like_clause} ORDER BY upload_time DESC"
                cursor.execute(sql, tuple([f"%{search_query.lower()}%"] * len(columns)))
        else:
            sql = f"SELECT * FROM {table_name} ORDER BY upload_time DESC"
            cursor.execute(sql)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Group rows by upload_time and remove upload_time from each row
        upload_time_index = all_columns.index("upload_time")
        grouped_data = {}
        for row in rows:
            key = row[upload_time_index]
            row_without_upload_time = row[:upload_time_index] + row[upload_time_index + 1:]
            grouped_data.setdefault(key, []).append(row_without_upload_time)

        return render_template('update_table.html', columns=columns, grouped_data=grouped_data, search_query=search_query, message=None)

    except Exception as e:
        traceback.print_exc()
        return render_template('update_table.html', columns=[], grouped_data={}, search_query=search_query, message=f"Error: {e}")


# Start the app
if __name__ == '__main__':
    app1.run(debug=True)

