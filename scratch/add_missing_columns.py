import pymysql

# Connect to the Cloud SQL Auth Proxy on localhost:3307
conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='Summer@69',
    database='garden'
)

try:
    with conn.cursor() as cursor:
        columns_to_add = [
            ("garden_updates", "temperature", "VARCHAR(255)"),
            ("garden_updates", "humidity", "VARCHAR(255)"),
            ("garden_updates", "needs_watering", "BOOLEAN DEFAULT FALSE"),
            ("garden_updates", "needs_fertilizer", "BOOLEAN DEFAULT FALSE"),
            ("garden_updates", "has_pests", "BOOLEAN DEFAULT FALSE"),
            ("garden_updates", "has_weeds", "BOOLEAN DEFAULT FALSE"),
            ("garden_updates", "has_disease", "BOOLEAN DEFAULT FALSE"),
            ("garden_updates", "needs_sunlight", "BOOLEAN DEFAULT FALSE"),
        ]
        
        for table, col, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")
                print(f"Added {col} to {table}")
            except Exception as e:
                print(f"Column {col} in {table} maybe exists or error: {e}")
                
    conn.commit()
    print("Database columns added successfully!")
finally:
    conn.close()
