import psycopg2

def get_db_connection(dbname, username, password, host='localhost', port='5432'):
    try:
        return psycopg2.connect(
            dbname=dbname,
            user=username,
            password=password,
            host=host,
            port=port
        )
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")