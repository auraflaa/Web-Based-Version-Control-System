from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL connection setup
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',  # or your database server
        user='root',       # your MySQL username
        password='Radhakrishna1',  # your MySQL password
        database='codehub'  # your database name
    )
    return connection

# Example route to fetch users
@app.route('/users', methods=['GET'])
def get_users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(users)

if __name__ == '__main__':
    app.run(debug=True)
