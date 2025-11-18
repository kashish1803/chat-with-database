import psycopg2
import pymysql

def get_database_schema(conn, database_name, db_type="mysql"):
    """
    Fetch full schema info (tables, columns, PKs, FKs) for MySQL or PostgreSQL.
    Returns a dictionary with tables, columns, types, primary keys, and foreign keys.
    """
    schema = {}

    try:
        with conn.cursor() as cursor:

            if db_type.lower() == "mysql":
                # ✅ MySQL Schema Fetch
                cursor.execute("SHOW TABLES;")
                tables = [t[0] for t in cursor.fetchall()]

                for table in tables:
                    cursor.execute(f"SHOW COLUMNS FROM {table};")
                    columns = cursor.fetchall()
                    schema[table] = {
                        "columns": [col[0] for col in columns],
                        "types": {col[0]: col[1] for col in columns},
                        "primary_keys": [col[0] for col in columns if col[3] == 'PRI']
                    }

                # Foreign Keys
                cursor.execute(f"""
                    SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = '{database_name}'
                    AND REFERENCED_TABLE_NAME IS NOT NULL;
                """)
                fkeys = cursor.fetchall()
                for table, col, ref_table, ref_col in fkeys:
                    schema.setdefault(table, {}).setdefault("foreign_keys", []).append({
                        "column": col,
                        "ref_table": ref_table,
                        "ref_column": ref_col
                    })

            elif db_type.lower() == "postgresql":
                # ✅ PostgreSQL Schema Fetch
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public';
                """)
                tables = [t[0] for t in cursor.fetchall()]

                for table in tables:
                    cursor.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = '{table}';
                    """)
                    cols = cursor.fetchall()
                    schema[table] = {
                        "columns": [c[0] for c in cols],
                        "types": {c[0]: c[1] for c in cols},
                        "primary_keys": []
                    }

                    # Primary Keys
                    cursor.execute(f"""
                        SELECT a.attname
                        FROM pg_index i
                        JOIN pg_attribute a ON a.attrelid = i.indrelid
                        AND a.attnum = ANY(i.indkey)
                        WHERE i.indrelid = '{table}'::regclass
                        AND i.indisprimary;
                    """)
                    pks = [r[0] for r in cursor.fetchall()]
                    schema[table]["primary_keys"] = pks

                    # Foreign Keys
                    cursor.execute(f"""
                        SELECT
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM
                            information_schema.table_constraints AS tc
                            JOIN information_schema.key_column_usage AS kcu
                              ON tc.constraint_name = kcu.constraint_name
                            JOIN information_schema.constraint_column_usage AS ccu
                              ON ccu.constraint_name = tc.constraint_name
                        WHERE
                            tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = '{table}';
                    """)
                    fks = cursor.fetchall()
                    schema[table]["foreign_keys"] = [
                        {"column": c, "ref_table": ft, "ref_column": fc}
                        for c, ft, fc in fks
                    ]

            else:
                raise ValueError(f"Unsupported database type: {db_type}")

        return schema

    except Exception as e:
        print(f"❌ Error fetching schema for {db_type}: {e}")
        return None
