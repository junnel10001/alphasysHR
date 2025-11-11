import os
import psycopg2
import bcrypt

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "alphasys"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def employee_access_exists(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM permissions WHERE permission_name = %s", ("employee_access",))
        return cur.fetchone() is not None

def role_permission_exists(conn, role_name, permission_name):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM role_permissions 
            JOIN roles ON role_permissions.role_id = roles.role_id 
            JOIN permissions ON role_permissions.permission_id = permissions.permission_id 
            WHERE roles.role_name = %s AND permissions.permission_name = %s
        """, (role_name, permission_name))
        return cur.fetchone() is not None

def create_employee_access_permission(conn):
    with conn.cursor() as cur:
        # Ensure employee_access permission exists
        cur.execute(
            """
            INSERT INTO permissions (permission_name, description)
            VALUES (%s, %s)
            """,
            ("employee_access", "Access to employee-specific dashboard and personal data")
        )
        # Ensure CRUD permissions for employee management exist
        cur.execute(
            """
            INSERT INTO permissions (permission_name, description)
            VALUES
                (%s, %s),
                (%s, %s),
                (%s, %s)
            ON CONFLICT (permission_name) DO NOTHING
            """,
            (
                "create_employee", "Create new employee records",
                "update_employee", "Update existing employee records",
                "delete_employee", "Delete employee records",
            ),
        )
        conn.commit()
        print("employee_access and CRUD permissions created.")

def assign_employee_access_to_role(conn):
    with conn.cursor() as cur:
        # Get role_id for employee role
        cur.execute("SELECT role_id FROM roles WHERE role_name = %s", ("employee",))
        role_result = cur.fetchone()
        
        if not role_result:
            print("Employee role not found. Creating employee role...")
            cur.execute(
                """
                INSERT INTO roles (role_name, description)
                VALUES (%s, %s)
                """,
                ("employee", "Regular employee with access to personal dashboard")
            )
            conn.commit()
            
            # Get the newly created role_id
            cur.execute("SELECT role_id FROM roles WHERE role_name = %s", ("employee",))
            role_result = cur.fetchone()
        
        role_id = role_result[0]
        
        # Get permission_id for employee_access
        cur.execute("SELECT permission_id FROM permissions WHERE permission_name = %s", ("employee_access",))
        permission_result = cur.fetchone()
        
        if not permission_result:
            print("employee_access permission not found.")
            return False
            
        permission_id = permission_result[0]
        
        # Check if the permission is already assigned to the role
        if role_permission_exists(conn, "employee", "employee_access"):
            print("employee_access permission already assigned to employee role.")
            return True
        
        # Assign the permission to the role
        cur.execute(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES (%s, %s)
            """,
            (role_id, permission_id)
        )
        conn.commit()
        print("employee_access permission assigned to employee role.")
        return True

def main():
    conn = get_connection()
    
    if not employee_access_exists(conn):
        create_employee_access_permission(conn)
        assign_employee_access_to_role(conn)
        # Assign CRUD permissions to admin role
        assign_permissions_to_admin(conn)
    else:
        print("employee_access permission already exists.")
        # Check if it's assigned to employee role
        if not role_permission_exists(conn, "employee", "employee_access"):
            assign_employee_access_to_role(conn)
        else:
            print("employee_access permission already assigned to employee role.")
    
    conn.close()

if __name__ == "__main__":
    main()