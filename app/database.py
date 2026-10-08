import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from app.config import Config


class Database:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        """Initialize connection pool"""
        config = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'pool_name': 'chatbot_pool',
            'pool_size': 10,
            'pool_reset_session': True,
            'autocommit': False,
            'use_pure': True,  # Use pure Python implementation
            'connection_timeout': 30
        }
        try:
            self._pool = mysql.connector.pooling.MySQLConnectionPool(**config)
        except Exception as e:
            print(f"Error initializing database pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                # Ensure all results are consumed
                try:
                    if conn.unread_result:
                        cursor = conn.cursor()
                        while cursor.nextset():
                            pass
                        cursor.close()
                except:
                    pass
                conn.close()

    def execute(self, query, params=None, fetch_one=False, fetch_all=False):
        """Execute a query and return results"""
        conn = None
        cursor = None
        try:
            conn = self._pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())

            result = None
            if fetch_one:
                result = cursor.fetchone()
                # Consume any remaining results
                while cursor.nextset():
                    pass
            elif fetch_all:
                result = cursor.fetchall()
                # Consume any remaining results
                while cursor.nextset():
                    pass
            else:
                result = cursor.rowcount
                # Consume any remaining results
                while cursor.nextset():
                    pass

            conn.commit()
            return result

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def test_connection(self):
        """Test database connection"""
        try:
            conn = self._pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False


# Create global database instance
db = Database()
