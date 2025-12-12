import psycopg2

class User:
    def __init__(self, db_config):
        self.db_config = db_config

    def connect(self):
        return psycopg2.connect(**self.db_config)

    def login(self, username, password):
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("""
                SELECT user_id, full_name, role_id
                FROM "User"
                WHERE username = %s AND password = %s;
            """, (username, password))

            row = cur.fetchone()
            cur.close()
            conn.close()

            return row

        except Exception as e:
            print("Error during login:", e)
            return None