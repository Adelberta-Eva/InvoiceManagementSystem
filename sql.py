import mysql.connector


def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Wqy2830363",
            database="InvoiceSystem",
            connection_timeout=30,
            charset='utf8mb4'  # 设置字符集为 utf8mb4
        )
        print("数据库连接成功")
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None


def insert_invoice(record, file_data):
    conn = connect_db()
    if not conn:
        print("❌ 数据库连接失败")
        return False

    cursor = None
    try:
        cursor = conn.cursor()

        # 插入语句字段名必须匹配数据库表结构
        sql = """
            INSERT INTO invoices (
                id, invoice_number, date, amount, project_name, image
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (*record, file_data)

        cursor.execute(sql, values)
        conn.commit()
        print("✅ 发票数据已成功插入数据库")
        return True

    except mysql.connector.Error as err:
        print(f"❌ 数据库错误: {err}")
        conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def search_invoices():
    """ 查询发票信息 """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, invoice_number, project_name, amount, date FROM invoices")
    results = cursor.fetchall()  # 获取所有查询结果
    cursor.close()
    conn.close()
    return results


# sql.py 中 get_invoice_file 方法保持不变
def get_invoice_file(invoice_id):
    try:
        conn = connect_db()
        if not conn:
            print("数据库连接失败")
            return None

        cursor = conn.cursor()
        cursor.execute("SELECT image FROM invoices WHERE id = %s", (invoice_id,))
        result = cursor.fetchone()
        if result:
            file_data = result[0]
            print(f"获取到文件数据，大小: {len(file_data)} 字节")
            return file_data
        else:
            print(f"未找到ID为 {invoice_id} 的发票记录")
            return None
    except Exception as e:
        print(f"获取文件数据时出错: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# sql.py 中添加筛选方法
def search_invoices_by_criteria(invoice_number=None, start_date=None, end_date=None, min_amount=None, max_amount=None,
                                project_name=None):
    conn = connect_db()
    cursor = conn.cursor()

    query = """
        SELECT id, invoice_number, date, amount, project_name 
        FROM invoices 
        WHERE 1=1
    """
    params = []

    if invoice_number:
        query += " AND invoice_number LIKE %s"
        params.append(f"%{invoice_number}%")

    if start_date:
        query += " AND date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND date <= %s"
        params.append(end_date)

    if min_amount is not None:
        query += " AND amount >= %s"
        params.append(min_amount)

    if max_amount is not None:
        query += " AND amount <= %s"
        params.append(max_amount)

    if project_name:
        query += " AND project_name LIKE %s"
        params.append(f"%{project_name}%")

    try:
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        return results

    except Exception as e:
        print(f"查询失败: {e}")
        return []

    finally:
        cursor.close()
        conn.close()
    return results
