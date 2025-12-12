class Role:
    def __init__(self, conn=None):
        """Pass an existing connection (from User) or create a new one"""
        self.conn = conn
        self.cursor = None
        if self.conn:
            self.cursor = self.conn.cursor()
        else:
            self.connect_db()

    def connect_db(self):
        """Connect to PostgreSQL database if no connection passed"""
        try:
            import psycopg2
            self.conn = psycopg2.connect(
                host="localhost",
                database="smartlibrary",
                user="postgres",        # your PostgreSQL username
                password="your_password" # your PostgreSQL password
            )
            self.cursor = self.conn.cursor()
            print("Role database connected successfully!")
        except Exception as e:
            print(f"Error connecting to database: {e}")

    def get_role_name(self, role_id):
        if not self.cursor:
            print("Cannot fetch role: No database connection")
            return None
        try:
            query = "SELECT role_name FROM Role WHERE role_id = %s"
            self.cursor.execute(query, (role_id,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"Error fetching role: {e}")
            return None

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()