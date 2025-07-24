import pytesseract
import cv2
import os,io
import uuid
import numpy as np
from pdf2image import convert_from_path
import sql  # 连接数据库的模块
from PIL import Image  # 用于处理ICC配置文件
import re
import gc
import test
import mysql.connector
# 导入数据库操作模块中的函数
from sql import (
    insert_invoice as sql_insert_invoice,
    get_invoice_file,
    search_invoices_by_criteria  # ← 我们重点需要的函数
)
def get_tesseract_path():
    """ 获取 Tesseract OCR 的本地路径 """
    return r"D:\tesseractOCR\tesseract.exe"  # 设置 tesseract.exe 的路径


# 设置 pytesseract 的路径
pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()

def clear_image_cache():
    """ 清理 Pillow 图像缓存 """
    gc.collect()  # 强制进行垃圾回收
def clear_cv_cache():
    """ 清理 OpenCV 缓存 """
    cv2.destroyAllWindows()  # 销毁所有 OpenCV 窗口，释放资源
def remove_iccp_profile(file_path):
    """ 去除图像文件中的 ICC 配置文件，保留原有功能并增强处理 """
    try:
        img = Image.open(file_path)

        # 删除任何 ICC 配置文件
        if 'icc_profile' in img.info:
            del img.info['icc_profile']

        # 转换为 RGB 图像并确保不嵌入ICC配置文件
        img = img.convert('RGB')

        # 确保保存为 JPEG 时没有配置文件
        new_file_path = file_path.replace(".png", "_cleaned.jpg")
        img.save(new_file_path, format='JPEG', icc_profile=None)  # 设置 icc_profile 为 None

        print(f"ICC 配置文件已成功移除，保存为: {new_file_path}")
        return new_file_path  # 返回无 ICC 配置文件的路径
    except Exception as e:
        print(f"处理图像时出错：{e}")
        return None

def compress_image(image, output_path, quality=85, scale_percent=50):
    """ 压缩图像：通过调整大小和降低图像质量来减少文件大小 """

    # 调整图像大小（缩小图像）
    height, width = image.shape[:2]
    new_width = int(width * scale_percent / 100)
    new_height = int(height * scale_percent / 100)
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # 使用 Pillow 保存为 JPEG 格式并设置质量（压缩）
    pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))  # 转换为 PIL 图像
    pil_image.save(output_path, 'JPEG', quality=quality)  # 保存并设置质量

    return output_path  # 返回压缩后的文件路径

from PyQt6.QtWidgets import QInputDialog


def get_invoice_file(invoice_id):
    """
    根据发票ID获取对应的发票文件二进制数据
    :param invoice_id: 发票ID
    :return: 发票文件的二进制数据
    """
    try:
        conn = sql.connector.connect(
            host="localhost",
            user="root",
            password="Wqy2830363",
            database="InvoiceSystem",
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM invoices WHERE id = %s", (invoice_id,))
        result = cursor.fetchone()
        if result:
            file_data = result[0]
            print(f"获取到文件数据，大小: {len(file_data)} 字节")

            # 尝试用PIL检查图片是否有效
            image = Image.open(io.BytesIO(file_data))
            print("图片格式:", image.format)
            return file_data
        else:
            print(f"未找到ID为 {invoice_id} 的发票记录")
            return None
    except Exception as e:
        print(f"获取文件数据时出错: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def export_image_from_db(invoice_id, output_path):
    """
    将数据库中的图片数据导出到本地文件
    :param invoice_id: 发票ID
    :param output_path: 输出文件路径
    :return: 导出是否成功
    """
    try:
        conn = sql.connector.connect(
            host="localhost",
            user="root",
            password="Wqy2830363",
            database="InvoiceSystem",
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM invoices WHERE id = %s", (invoice_id,))
        result = cursor.fetchone()
        if result:
            file_data = result[0]
            with open(output_path, "wb") as f:
                f.write(file_data)
            print(f"图片已导出到 {output_path}")
            return True
        else:
            print(f"未找到ID为 {invoice_id} 的发票记录")
            return False
    except Exception as e:
        print(f"导出图片时出错: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def process_invoice_image(file_path):
    """
    处理发票文件，提取关键信息
    :param file_path: 图片或 PDF 文件路径
    :return: 提取的字段信息字典
    """
    extracted_data = {}

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在！")
        return None

    # 如果是 PNG 文件，去除 ICC 配置文件
    if file_path.lower().endswith(".png"):
        cleaned_file_path = remove_iccp_profile(file_path)
        if not cleaned_file_path:
            print(f"去除 ICC 配置文件失败: {file_path}")
            return None
        file_path = cleaned_file_path  # 使用清理后的文件

    print(f"正在处理文件: {file_path}")

    # 清理缓存
    clear_image_cache()

    # 处理 PDF 或 图片
    try:
        if file_path.lower().endswith(".pdf"):
            images = convert_from_path(file_path)
            if not images:
                print("无法解析 PDF")
                return None
            image = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)  # 仅处理第一页
        else:
            image = cv2.imread(file_path)

        # 检查 OpenCV 是否成功加载图片
        if image is None:
            print(f"无法加载图片: {file_path}")
            return None

        print("图片加载成功，正在转换为灰度图...")
        # 转换为灰度图，提高 OCR 识别率
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        print("正在执行 OCR 识别...")
        # OCR 识别
        text = pytesseract.image_to_string(gray, lang="chi_sim")

        print("OCR 提取的文本: ")
        print(text)  # 打印 OCR 提取的文本，帮助调试
    except cv2.error as e:
        print(f"OpenCV 错误: {e}")
        return None
    except pytesseract.TesseractError as e:
        print(f"Tesseract 错误: {e}")
        return None
    except Exception as e:
        print(f"图像处理出错: {e}")
        return None

    # 清理缓存
    clear_image_cache()

    # 解析提取内容
    extracted_data["invoice_number"] = extract_invoice_number(text)
    extracted_data["date"] = extract_invoice_date(text)
    extracted_data["amount"] = extract_invoice_amount(text)
    extracted_data["project_name"] = extract_invoice_project(text)

    # 如果 OCR 没有提取到项目名称，弹出输入框让用户手动输入
    if not extracted_data["project_name"]:
        print("未提取到项目名称，请手动输入：")
        project_name, ok = QInputDialog.getText(None, "手动输入项目名称", "请输入项目名称:")
        if ok and project_name:
            extracted_data["project_name"] = project_name
        else:
            extracted_data["project_name"] = "未知"

    print("提取的发票信息: ")
    print(extracted_data)  # 打印提取的数据，帮助调试

    return extracted_data



def extract_invoice_number(text):
    """ 提取发票号 """
    print("正在提取发票号...")
    # 修改正则表达式来适应发票号的格式
    match = re.search(r"(?:发票号码|发票号)[:：]?\s*(\d{8,20})", text)
    if match:
        print(f"提取的发票号: {match.group(1)}")
        return match.group(1)
    else:
        print("未能提取到发票号")
        return "未知"


def extract_invoice_date(text):
    """ 提取日期 """
    print("正在提取日期...")
    # 改进日期正则表达式，适应多种日期格式
    match = re.search(r"(\d{4}[-年/.]\d{1,2}[-月/.]\d{1,2})", text)
    if match:
        print(f"提取的日期: {match.group(1)}")
        return match.group(1)
    else:
        print("未能提取到日期")
        return "未知"


def extract_invoice_amount(text):
    """ 提取金额 """
    print("正在提取金额...")
    match = re.search(r"价税合计\s*[\D]*(\d+[.,]?\d*)", text)
    if match:
        amount = match.group(1)
        # 清理金额中的额外符号
        return amount.rstrip('.')
    return "未知"


def extract_invoice_project(text):
    """ 提取资金项目 """
    print("正在提取项目名称...")
    print(f"传入的文本: {text}")  # 打印输入文本，帮助调试
    match = re.search(r"项目名称\s*([^\d]+)", text)
    if match:
        project_name = match.group(1).strip()
        # 优化：排除不必要的部分，提取项目的实际名称
        if '规格型号' in project_name:
            project_name = project_name.split('规格型号')[0].strip()
        print(f"提取的项目名称: {project_name}")  # 打印提取的项目名称
        return project_name
    return "未知"


# 原样保留你的 imports 和函数

import uuid

import uuid
import backend  # 假设 backend.py 包含了 insert_invoice 函数


def insert_invoice(data, file_data):
    """将发票信息存入数据库，包括图片二进制文件"""

    invoice_id = uuid.uuid4().hex[:16]  # 生成唯一 ID

    try:
        if not file_data:
            print("❌ 文件数据为空，无法插入数据库")
            return None

        # 打印调试信息
        print(f"file_data 类型: {type(file_data)}")
        print(f"file_data 大小: {len(file_data)} 字节")

        # 构造数据元组
        formatted_date = format_date(data.get("date", ""))
        if not formatted_date:
            print("❌ 日期格式错误，无法继续插入操作")
            return None

        record = (
            invoice_id,
            data.get("invoice_number", "未知"),
            formatted_date,  # 使用转换后的日期
            float(data.get("amount", 0)),  # 确保金额为浮点数
            data.get("project_name", "未知")
        )

        # 调用数据库插入函数
        try:
            backend.sql.insert_invoice(record, file_data)  # 假设 backend.py 包含 sql 模块
            print("✅ 数据成功插入数据库！")
            return invoice_id
        except Exception as e:
            print(f"❌ 插入数据时发生错误: {e}")
            return None

    except Exception as e:
        print(f"❌ 插入数据时发生错误: {e}")
        return None
    # backend.py 中 insert_invoice 方法末尾添加
    if success:
        return {"status": "success", "data": record}
    else:
        return {"status": "error", "message": "插入失败"}


def get_file_data_from_db(invoice_id):
    """ 从数据库获取文件数据并检查其内容 """
    try:
        conn = sql.connect_db()  # 连接到数据库
        cursor = conn.cursor()
        cursor.execute("SELECT file_data FROM invoices WHERE id = %s", (invoice_id,))
        result = cursor.fetchone()  # 获取查询结果
        if result:
            file_data = result[0]  # 获取文件数据
            print(f"file_data 类型: {type(file_data)}")
            print(f"file_data 大小: {len(file_data)} 字节")
            # 打印一些前几个字节，以确保数据没有损坏（不建议直接打印整个二进制内容）
            print(f"file_data 前10个字节: {file_data[:10]}")
            return file_data
        else:
            print("未找到该 ID 对应的数据")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"查询数据库时出错: {e}")
    return None


def save_file_data_to_disk(file_data, output_file_path):
    """ 将 file_data 保存为本地文件以进行检查 """
    try:
        with open(output_file_path, "wb") as f:
            f.write(file_data)  # 将二进制数据写入文件
        print(f"文件已成功保存到 {output_file_path}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

from datetime import datetime

from datetime import datetime

from datetime import datetime


def format_date(date_str):
    if not date_str:
        print("警告: 日期字符串为空")
        return None

    # 去除可能存在的多余字符，例如中文"日"
    date_str = date_str.replace('日', '').strip()

    # 尝试不同的日期格式进行解析
    for fmt in ("%Y年%m月%d", "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d')  # 转换为MySQL可接受的日期格式
        except ValueError:
            continue
    print(f"警告: 无法解析日期 '{date_str}'")
    return None

    def matches_criteria(invoice, invoice_number=None, start_date=None, end_date=None, min_amount=None, max_amount=None,
                         project_name=None):
        """
        判断单个发票是否符合指定的筛选条件
        """
        if invoice_number and invoice.get('invoice_number') != invoice_number:
            return False
        if start_date and invoice.get('date') < start_date:
            return False
        if end_date and invoice.get('date') > end_date:
            return False
        if min_amount is not None and invoice.get('amount', 0) < min_amount:
            return False
        if max_amount is not None and invoice.get('amount', 0) > max_amount:
            return False
        if project_name and project_name.lower() not in invoice.get('project_name', '').lower():
            return False
        return True

    def search_invoices_by_criteria(invoices, invoice_number=None, start_date=None, end_date=None, min_amount=None,
                                    max_amount=None, project_name=None):
        """
        对内存中的发票列表进行条件过滤
        """
        return [
            inv for inv in invoices
            if matches_criteria(inv,
                                invoice_number=invoice_number,
                                start_date=start_date,
                                end_date=end_date,
                                min_amount=min_amount,
                                max_amount=max_amount,
                                project_name=project_name)
        ]

# backend.py
from sql import connect_db
def search_invoices(criteria):
    conn = None
    cursor = None
    try:
        conn = sql.connect_db()
        if not conn:
            print("❌ 数据库连接失败")
            return []

        cursor = conn.cursor()

        query = "SELECT id, invoice_number, date, amount, project_name FROM invoices WHERE 1=1"
        params = []

        if criteria['start_date'] and criteria['end_date']:
            query += " AND date BETWEEN %s AND %s"
            params.extend([criteria['start_date'], criteria['end_date']])

        if criteria['project_name']:
            query += " AND project_name LIKE %s"
            params.append(f"%{criteria['project_name']}%")

        if criteria['invoice_number']:
            query += " AND invoice_number LIKE %s"
            params.append(f"%{criteria['invoice_number']}%")

        if criteria['min_amount'] is not None:
            query += " AND amount >= %s"
            params.append(criteria['min_amount'])

        if criteria['max_amount'] is not None:
            query += " AND amount <= %s"
            params.append(criteria['max_amount'])

        cursor.execute(query, params)
        results = cursor.fetchall()
        return results

    except Exception as e:
        print(f"数据库查询出错: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_invoice_file(invoice_id):
    """
    根据发票ID获取对应的发票文件二进制数据
    :param invoice_id: 发票ID
    :return: 发票文件的二进制数据
    """
    try:
        conn = mysql.connector.connect(  # 使用mysql.connector.connect
            host="localhost",
            user="root",
            password="Wqy2830363",
            database="InvoiceSystem",
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM invoices WHERE id = %s", (invoice_id,))
        result = cursor.fetchone()
        if result:
            file_data = result[0]
            print(f"获取到文件数据，大小: {len(file_data)} 字节")

            # 尝试用PIL检查图片是否有效
            try:
                image = Image.open(io.BytesIO(file_data))
                print(f"图片格式: {image.format}, 大小: {image.size}")
                return file_data
            except Exception as e:
                print(f"PIL检查图片出错: {e}")
                return None
        else:
            print(f"未找到ID为 {invoice_id} 的发票记录")
            return None
    except Exception as e:
        print(f"获取文件数据时出错: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_statistics(start_date, end_date, keyword=None):
    """
    获取指定日期范围和关键词的统计信息
    :param start_date: 开始日期 (字符串格式: yyyy-MM-dd)
    :param end_date: 结束日期 (字符串格式: yyyy-MM-dd)
    :param keyword: 模糊查询关键词 (可选)
    :return: 元组 (发票张数, 总金额) 或 None
    """
    try:
        conn = sql.connect_db()
        if not conn:
            print("数据库连接失败")
            return None

        cursor = conn.cursor()

        query = """
            SELECT COUNT(*), SUM(amount)
            FROM invoices
            WHERE date BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if keyword:
            query += " AND (invoice_number LIKE %s OR project_name LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        cursor.execute(query, params)
        result = cursor.fetchone()

        if result:
            count, total_amount = result
            return (count, total_amount)
        else:
            return None

    except Exception as e:
        print(f"统计查询出错: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()