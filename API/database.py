import psycopg2
import dotenv
import os

dotenv.load_dotenv()


def connect_to_db():
    try:
        # Define your connection parameters
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )

        # Create a cursor object
        cursor = connection.cursor()

        # Print PostgreSQL Connection properties
        print(connection.get_dsn_parameters(), "\n")

        # Execute a test query
        cursor.execute("SELECT version();")

        # Fetch result
        record = cursor.fetchone()
        print("You are connected to - ", record, "\n")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        # Closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


if __name__ == "__main__":
    connect_to_db()
