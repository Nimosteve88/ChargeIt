import psycopg2

# Database connection details
host = "chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com"
port = "5432"  # Default PostgreSQL port
dbname = "initial_db"
user = "postgres"
password = "ChargeIt2024"


# ##############################TEST CONNECTION ########################################
try:
    connection = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    print("Connected to the database successfully")
except Exception as e:
    print(f"Error connecting to the database: {e}")


# ##############################CREATE TABLES ########################################
# try:
#     cursor = connection.cursor()
#     create_table_query = '''
#     CREATE TABLE IF NOT EXISTS employees (
#         id SERIAL PRIMARY KEY,
#         name VARCHAR(100),
#         age INTEGER,
#         department VARCHAR(50)
#     )
#     '''
#     cursor.execute(create_table_query)
#     connection.commit()
#     print("Table created successfully")
# except Exception as e:
#     print(f"Error creating table: {e}")
# finally:
#     cursor.close()


# ##############################INSERT DATA ########################################
try:
    cursor = connection.cursor()
    insert_query = '''
    INSERT INTO employees (name, age, department) VALUES (%s, %s, %s)
    '''
    data_to_insert = ('John Doooo', 50, 'Engineering')
    cursor.execute(insert_query, data_to_insert)
    connection.commit()
    print("Data inserted successfully")
except Exception as e:
    print(f"Error inserting data: {e}")
finally:
    cursor.close()


# ##############################FETCH DATA ########################################
try:
    cursor = connection.cursor()
    select_query = '''
    SELECT * FROM employees
    '''
    cursor.execute(select_query)
    records = cursor.fetchall()
    for record in records:
        print(record)
except Exception as e:
    print(f"Error querying data: {e}")
finally:
    cursor.close()

# ##############################UPDATE DATA ########################################
# try:
#     cursor = connection.cursor()
#     update_query = '''
#     UPDATE employees SET age = %s WHERE name = %s
#     '''
#     data_to_update = (35, 'John Doe')
#     cursor.execute(update_query, data_to_update)
#     connection.commit()
#     print("Data updated successfully")
# except Exception as e:
#     print(f"Error updating data: {e}")
# finally:
#     cursor.close()


# ##############################DELETE DATA ########################################
# try:
#     cursor = connection.cursor()
#     delete_query = '''
#     DELETE FROM employees WHERE name = %s
#     '''
#     data_to_delete = ('John Doe',)
#     cursor.execute(delete_query, data_to_delete)
#     connection.commit()
#     print("Data deleted successfully")
# except Exception as e:
#     print(f"Error deleting data: {e}")
# finally:
#     cursor.close()

# Close the connection
# try:
#     if connection:
#         connection.close()
#         print("Database connection closed")
# except Exception as e:
#     print(f"Error closing the database connection: {e}")
