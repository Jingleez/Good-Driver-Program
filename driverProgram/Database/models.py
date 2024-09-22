import mysql.connector
from flask import current_app
from mysql.connector import Error

class DBConnection:
    def __init__(self):
        self.connection = None

    def init_app(self, app):
        """Initialize the database connection with the Flask app's configuration."""
        self.initialize(app)

    def initialize(self, app):
        try:
            self.connection = mysql.connector.connect(
                host=app.config['DB_HOST'],
                user=app.config['DB_USER'],
                password=app.config['DB_PASSWORD'],
                database=app.config['DB_NAME']
            )
            if self.connection.is_connected():
                print("Successfully connected to the database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None

    def get_connection(self):
        if self.connection and self.connection.is_connected():
            return self.connection
        else:
            print("Reconnecting to the database...")
            self.initialize(current_app)
            return self.connection

# Initialize a single DBConnection instance
db_connection = DBConnection()

# Define your utility functions
def ifUsernameExist(user='NULL'):
    if user == 'NULL':
        return False
    cursor = db_connection.get_connection().cursor()
    sql = "SELECT user_name FROM user WHERE user_name = %s"
    val = (user, )
    cursor.execute(sql, val)
    row = cursor.fetchone()
    cursor.close()
    return False if row is None or row[0] is None else True

def pwdCheck(user='NULL', pwd='NULL'):
    if user == 'NULL' or pwd == 'NULL':
        return False
    cursor = db_connection.get_connection().cursor()
    sql = 'SELECT role FROM user WHERE user_name = %s'
    val = (user, )
    cursor.execute(sql, val)
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return False
    role = row[0]
    sql = f'SELECT pwd FROM {role} WHERE user = %s'
    val = (user, )
    cursor.execute(sql, val)
    current_password = cursor.fetchone()
    cursor.close()
    if current_password is None:
        return False
    return pwd == current_password[0]

def getRole(user='NULL'):
    if user == 'NULL':
        return None
    cursor = db_connection.get_connection().cursor()
    sql = 'SELECT role FROM user WHERE user_name = %s'
    val = (user, )
    cursor.execute(sql, val)
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None
