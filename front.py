from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, \
    QFileDialog, QTableWidget, QTableWidgetItem, QListWidgetItem,QLineEdit, QGridLayout, QDateEdit, QTextEdit
from PyQt6.QtCore import QDate, Qt
import backend  # 导入后端处理模块
from PyQt6.QtGui import QPixmap
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QFileDialog, QMessageBox, QLineEdit, QLabel,QDialog
import uuid
import os,io
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
class InvoiceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能发票管理系统")
        self.setGeometry(200, 100, 950, 650)
        self.setStyleSheet("background-color: #f0f0f5; font-size: 14px; color: #333;")

        # 初始化图像预览区域
        self.imagePreviewLabel = QLabel("图片预览区域", self)
        self.imagePreviewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagePreviewLabel.setStyleSheet("border: 1px solid #ccc; padding: 10px; background: white")
        self.setStyleSheet("font-family: 'Microsoft YaHei';")
        self.your_label = QLabel("正确的文本内容")

        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)  # 创建一个新的水平布局作为主布局


        # 侧边导航栏
        sidebar = QVBoxLayout()
        sidebar.setSpacing(15)

        sidebar_buttons = {
            "📤 上传发票": 0,
            "🔍 查询发票": 1,
            "📊 统计分析": 2,
            "📞 联系开发者": 3
        }

        for text, index in sidebar_buttons.items():
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton { 
                    background-color: #007BFF; color: white; border-radius: 5px; 
                    font-weight: bold; 
                } 
                QPushButton:hover { 
                    background-color: #0056b3; 
                } 
            """)
            btn.clicked.connect(lambda _, i=index: self.stack.setCurrentIndex(i))
            sidebar.addWidget(btn)

        # 右侧内容区域
        self.stack = QStackedWidget()
        self.stack.addWidget(self.createUploadPage())  # 上传发票
        self.stack.addWidget(self.createSearchPage())  # 查询发票
        self.stack.addWidget(self.createStatsPage())  # 统计分析
        self.stack.addWidget(self.createContactPage())  # 联系开发者

        layout.addLayout(sidebar, 1)
        layout.addWidget(self.stack, 4)

        # 添加图像预览标签到主布局（假设你想把它放在最底部）
        layout.addWidget(self.imagePreviewLabel, 1)  # 添加到现有布局的最后一行

        self.setLayout(layout)  # 设置窗口的主布局
        self.stack.currentChanged.connect(self.clear_preview_on_page_change)

    def on_invoice_row_clicked(self, row, column):
        """当用户点击查询结果表格中的一行时触发此函数"""
        invoice_id_item = self.resultTable.item(row, 0)  # 假设第一列是 ID
        if invoice_id_item:
            invoice_id = invoice_id_item.text()
            img_data = backend.get_invoice_file(invoice_id)  # 调用后端方法获取图片
            if img_data:
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                self.imagePreviewLabel.setPixmap(pixmap.scaledToWidth(300))  # 缩放显示
            else:
                self.imagePreviewLabel.setText("无法加载图片")
        self.imagePreviewLabel.clear()
        self.imagePreviewLabel.setText("图片预览区域")

    def createUploadPage(self):
        """上传发票页面"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        self.uploadLabel = QLabel("拖拽文件到此处或点击选择文件")
        self.uploadLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.uploadLabel.setStyleSheet(""" 
            border: 2px dashed #007BFF; padding: 20px;
            font-size: 16px; background-color: #ffffff; color: #333;
        """)
        layout.addWidget(self.uploadLabel)

        self.uploadBtn = QPushButton("选择文件")
        self.uploadBtn.setFixedHeight(40)
        self.uploadBtn.setStyleSheet("background-color: #28a745; color: white; border-radius: 5px; font-weight: bold;")
        self.uploadBtn.clicked.connect(self.uploadFile)
        layout.addWidget(self.uploadBtn)

        page = QWidget()
        page.setLayout(layout)
        return page

    def uploadFile(self):
        """文件上传并处理"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择发票", "",
                                                   "Images (*.png *.jpg *.jpeg);;PDF Files (*.pdf)")
        if file_path:
            print(f"文件路径: {file_path}")  # 打印文件路径
            self.uploadLabel.setText(f"文件上传成功: {file_path.split('/')[-1]}")
            try:
                extracted_data = backend.process_invoice_image(file_path)
                if extracted_data:
                    self.showExtractedData(extracted_data, file_path)
            except Exception as e:
                print(f"处理文件时发生错误: {e}")
                self.uploadLabel.setText("文件处理失败，请重试。")


    def showExtractedData(self, extracted_data, file_path):
        """显示提取的发票信息并允许用户修改"""
        self.invoice_data = extracted_data  # 存储提取的数据
        self.file_path = file_path  # 存储文件路径
        layout = QVBoxLayout()

        # 假设提取数据包含以下字段（可以根据实际返回格式调整）
        self.projectNameInput = QLineEdit(extracted_data.get('project_name', ''))
        layout.addWidget(QLabel("项目名称"))
        layout.addWidget(self.projectNameInput)

        self.amountInput = QLineEdit(extracted_data.get('amount', ''))
        layout.addWidget(QLabel("金额"))
        layout.addWidget(self.amountInput)

        self.dateInput = QLineEdit(extracted_data.get('date', ''))
        layout.addWidget(QLabel("日期"))
        layout.addWidget(self.dateInput)

        self.invoiceNumberInput = QLineEdit(extracted_data.get('invoice_number', ''))
        layout.addWidget(QLabel("票号"))
        layout.addWidget(self.invoiceNumberInput)

        # 创建一个确认按钮
        confirmBtn = QPushButton("确认修改")
        confirmBtn.clicked.connect(self.confirmModification)
        layout.addWidget(confirmBtn)

        # 创建一个新的弹窗，显示识别的信息
        self.confirmWindow = QWidget()
        self.confirmWindow.setWindowTitle("确认修改")
        self.confirmWindow.setGeometry(400, 200, 400, 300)
        self.confirmWindow.setLayout(layout)
        self.confirmWindow.show()

    def confirmModification(self):
        """确认修改并存储到数据库"""
        # 获取用户修改的内容
        modified_data = {
            "invoice_number": self.invoiceNumberInput.text(),
            "date": self.dateInput.text(),
            "amount": self.amountInput.text(),
            "project_name": self.projectNameInput.text()
        }

        # 获取文件数据（在此示例中，使用的是上传的文件路径，可以根据需求调整）
        file_data = None
        if self.file_path:
            with open(self.file_path, 'rb') as f:
                file_data = f.read()

        # 将数据存入数据库
        invoice_id = backend.insert_invoice(modified_data, file_data)

        # 关闭确认窗口
        self.confirmWindow.close()

    def createSearchPage(self):
        """查询发票页面"""
        layout = QVBoxLayout()
        gridLayout = QGridLayout()

        # 添加项目名称输入框
        gridLayout.addWidget(QLabel("项目名称"), 0, 0)
        self.projectInput = QLineEdit()
        gridLayout.addWidget(self.projectInput, 0, 1)

        # 添加票号输入框
        gridLayout.addWidget(QLabel("票号"), 0, 2)
        self.invoiceNumberInput = QLineEdit()
        gridLayout.addWidget(self.invoiceNumberInput, 0, 3)

        # 添加开始日期和结束日期选择器
        gridLayout.addWidget(QLabel("📅 开始日期"), 1, 0)
        self.startDate = QDateEdit()
        self.startDate.setCalendarPopup(True)
        self.startDate.setDate(QDate.currentDate().addMonths(-1))
        gridLayout.addWidget(self.startDate, 1, 1)

        gridLayout.addWidget(QLabel("📅 结束日期"), 1, 2)
        self.endDate = QDateEdit()
        self.endDate.setCalendarPopup(True)
        self.endDate.setDate(QDate.currentDate())
        gridLayout.addWidget(self.endDate, 1, 3)

        # 添加金额范围输入框
        gridLayout.addWidget(QLabel("💰 最小金额"), 2, 0)
        self.minAmountInput = QLineEdit()
        gridLayout.addWidget(self.minAmountInput, 2, 1)

        gridLayout.addWidget(QLabel("💰 最大金额"), 2, 2)
        self.maxAmountInput = QLineEdit()
        gridLayout.addWidget(self.maxAmountInput, 2, 3)

        # 添加查询按钮
        self.searchBtn = QPushButton("🔍 查询")
        self.searchBtn.setFixedHeight(40)
        self.searchBtn.setStyleSheet("background-color: #ffc107; color: black; border-radius: 5px; font-weight: bold;")
        self.searchBtn.clicked.connect(self.on_search_clicked)
        layout.addLayout(gridLayout)
        layout.addWidget(self.searchBtn)

        # 添加表格显示查询结果
        self.resultTable = QTableWidget(0, 6)
        self.resultTable.setHorizontalHeaderLabels(["ID", "票号", "日期", "金额", "项目", "查看"])
        self.resultTable.setStyleSheet("background-color: white; color: black;")
        layout.addWidget(self.resultTable)

        # 添加图像预览标签
        self.imagePreviewLabel = QLabel("图片预览区域")
        self.imagePreviewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagePreviewLabel.setStyleSheet("border: 1px solid #ccc; padding: 10px; background: white")
        layout.addWidget(self.imagePreviewLabel)

        # 绑定表格点击事件
        self.resultTable.cellClicked.connect(self.on_invoice_row_clicked)

        page = QWidget()
        page.setLayout(layout)
        return page

    def update_invoice_list(self, invoices):
        """ 更新发票列表显示 """
        self.invoice_list_widget.clear()

        for invoice in invoices:
            item_text = f"{invoice['invoice_number']} - {invoice['project_name']} - {invoice['date']} - ￥{invoice['amount']}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, invoice['id'])
            self.invoice_list_widget.addItem(list_item)

        self.invoice_list_widget.itemClicked.connect(self.view_invoice)

    def searchButtonClicked(self):
        # 调用 backend 中的查询方法
        criteria = {}  # 此处可以增加筛选条件传递
        results = backend.search_invoices(criteria)

        # 更新表格显示
        self.result_table.setRowCount(len(results))
        for row, record in enumerate(results):
            for col, data in enumerate(record):
                self.result_table.setItem(row, col, QTableWidgetItem(str(data)))
            # 添加“查看”按钮
            view_button = QPushButton("查看")
            view_button.clicked.connect(lambda _, invoice_id=record[0]: self.view_image(invoice_id))
            self.result_table.setCellWidget(row, 5, view_button)

    def show_invoice_image(self, invoice_id):
        image_data = backend.get_invoice_file(invoice_id)
        if not image_data:
            QMessageBox.warning(self, "警告", "无法加载发票文件")
            return

        # 尝试用PIL加载图片并检查格式
        try:
            image = Image.open(io.BytesIO(image_data))
            print(f"图片格式: {image.format}, 大小: {image.size}")
        except Exception as e:
            print(f"PIL加载图片出错: {e}")
            QMessageBox.warning(self, "警告", f"PIL加载图片出错: {e}")
            return

        # 尝试将图片数据保存到本地文件
        temp_file_path = f"temp_invoice_{invoice_id}.jpg"
        try:
            # 使用PIL保存图片到临时文件
            with open(temp_file_path, "wb") as f:
                image.save(f, format=image.format)
            print(f"图片已保存到 {temp_file_path}")
        except Exception as e:
            print(f"保存图片时出错: {e}")
            QMessageBox.warning(self, "警告", f"保存图片时出错: {e}")
            return

        # 尝试用QPixmap加载图片
        pixmap = QPixmap()
        if pixmap.load(temp_file_path):
            dialog = QDialog(self)
            dialog.setWindowTitle(f"发票预览 - ID: {invoice_id}")
            layout = QVBoxLayout(dialog)

            label = QLabel()
            label.setPixmap(pixmap.scaledToWidth(600))  # 缩放图片以适应宽度
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中显示图片

            layout.addWidget(label)
            dialog.setLayout(layout)
            dialog.exec()
        else:
            QMessageBox.warning(self, "警告", "QPixmap无法加载图片")

        # 删除临时文件
        try:
            os.remove(temp_file_path)
            print(f"临时文件 {temp_file_path} 已删除")
        except Exception as e:
            print(f"删除临时文件时出错: {e}")
        self.imagePreviewLabel.clear()
        self.imagePreviewLabel.setText("图片预览区域")
    def view_invoice(self, item):
        """ 查看发票图片文件 """
        invoice_id = item.data(Qt.UserRole)
        from sql import get_invoice_file
        file_data = get_invoice_file(invoice_id)
        if file_data:
            # 保存文件到本地并打开
            file_path = f"temp_invoice_{invoice_id}.png"
            with open(file_path, "wb") as f:
                f.write(file_data)
            os.startfile(file_path)
        else:
            QMessageBox.warning(self, "错误", "无法获取发票图片文件。")

    def createStatsPage(self):
        """统计分析页面"""
        layout = QVBoxLayout()
        gridLayout = QGridLayout()

        # 添加日期范围选择器
        gridLayout.addWidget(QLabel("开始日期"), 0, 0)
        self.statsStartDate = QDateEdit()
        self.statsStartDate.setCalendarPopup(True)
        self.statsStartDate.setDate(QDate.currentDate().addMonths(-1))
        gridLayout.addWidget(self.statsStartDate, 0, 1)

        gridLayout.addWidget(QLabel("结束日期"), 0, 2)
        self.statsEndDate = QDateEdit()
        self.statsEndDate.setCalendarPopup(True)
        self.statsEndDate.setDate(QDate.currentDate())
        gridLayout.addWidget(self.statsEndDate, 0, 3)

        # 添加文字输入框用于模糊查询
        gridLayout.addWidget(QLabel("关键词"), 1, 0)
        self.statsKeywordInput = QLineEdit()
        gridLayout.addWidget(self.statsKeywordInput, 1, 1, 1, 3)

        # 添加统计按钮
        self.statsBtn = QPushButton("统计")
        self.statsBtn.clicked.connect(self.show_statistics)
        gridLayout.addWidget(self.statsBtn, 2, 0, 1, 4)

        # 添加显示统计结果的区域
        self.statsResultLabel = QLabel("统计结果将在这里显示")
        self.statsResultLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statsResultLabel.setStyleSheet("border: 1px solid #ccc; padding: 10px; background: white")
        layout.addLayout(gridLayout)
        layout.addWidget(self.statsResultLabel)

        page = QWidget()
        page.setLayout(layout)
        return page

    def show_statistics(self):
        start_date = self.statsStartDate.date().toString("yyyy-MM-dd")
        end_date = self.statsEndDate.date().toString("yyyy-MM-dd")
        keyword = self.statsKeywordInput.text().strip()

        # 调用后端统计方法
        result = backend.get_statistics(start_date, end_date, keyword)

        if result:
            count, total_amount = result
            self.statsResultLabel.setText(f"统计结果：共 {count} 张发票，总金额：{total_amount:.2f} 元")

            # 设置 Matplotlib 使用中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 用黑体显示中文
            plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

            # 创建图表
            fig, ax = plt.subplots(figsize=(6, 6))  # 设置图表大小
            ax.pie([total_amount], labels=[f"总金额: {total_amount:.2f}"], autopct='%1.1f%%',
                   textprops={'fontsize': 14, 'fontweight': 'bold'})  # 增大字体大小并加粗
            ax.set_title(f"统计结果 ({count} 张发票)", fontsize=16, fontweight='bold')  # 增大标题字体大小并加粗
            ax.axis('equal')  # 保证饼图为圆形

            # 调整布局以确保标签不被裁剪
            plt.tight_layout()

            # 将图表转换为 QPixmap 并显示
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300)  # 设置高分辨率
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            scaled_pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            self.imagePreviewLabel.setPixmap(scaled_pixmap)

        else:
            self.statsResultLabel.setText("未找到符合条件的发票")
    def generate_statistics_chart(self, result):
        # 创建图表
        fig, ax = plt.subplots()
        ax.pie([result[1]], labels=[f"总金额: {result[1]:.2f}"], autopct='%1.1f%%')
        ax.set_title(f"统计结果 ({result[0]} 张发票)")

        # 将图表转换为 QPixmap 并显示
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.read())
        self.imagePreviewLabel.setPixmap(pixmap.scaledToWidth(300))
    def createContactPage(self):
        """联系开发者页面"""
        layout = QVBoxLayout()

        # 添加开发者信息
        info_label = QLabel("智会2201班 巫青忆 学号：202221130276")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; margin-bottom: 20px;")
        layout.addWidget(info_label)

        # 添加信息反馈输入框和按钮
        feedback_layout = QVBoxLayout()
        feedback_label = QLabel("信息反馈：")
        feedback_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        feedback_layout.addWidget(feedback_label)

        self.feedback_edit = QTextEdit()
        self.feedback_edit.setStyleSheet("font-size: 14px; padding: 10px;")
        feedback_layout.addWidget(self.feedback_edit)

        submit_btn = QPushButton("提交反馈")
        submit_btn.setStyleSheet(
            "background-color: #007BFF; color: white; border-radius: 5px; padding: 10px; font-size: 14px;")
        submit_btn.clicked.connect(self.submit_feedback)
        feedback_layout.addWidget(submit_btn)

        layout.addLayout(feedback_layout)

        page = QWidget()
        page.setLayout(layout)
        return page

    def submit_feedback(self):
        """提交反馈"""
        feedback = self.feedback_edit.toPlainText()
        if feedback.strip():
            try:
                # 发送反馈邮件
                self.send_email("2311446274@qq.com", "反馈信息", feedback)
                QMessageBox.information(self, "反馈提交", "感谢您的反馈！我们会尽快处理。")
                self.feedback_edit.clear()
            except Exception as e:
                QMessageBox.warning(self, "反馈提交", f"提交反馈时出错：{str(e)}")
        else:
            QMessageBox.warning(self, "反馈提交", "请输入反馈内容。")

    def send_email(self, to_addr, subject, body):
        """发送邮件"""
        from_addr = "2311446274@qq.com"  # 替换为你的邮箱地址
        password = "XXXXXXXXX"  #这里不具体实现就用的假的

        # 创建邮件内容
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject

        # 添加邮件正文
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 发送邮件
        try:
            server = smtplib.SMTP_SSL("smtp.163.com", 465)  # 使用163邮箱的SMTP服务器
            server.login(from_addr, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            server.quit()
        except Exception as e:
            raise Exception(f"发送邮件时出错：{str(e)}")

    def submit_feedback(self):
        """提交反馈"""
        feedback = self.feedback_edit.toPlainText()
        if feedback.strip():
            # 这里可以添加将反馈信息发送给开发者的逻辑，例如发送邮件等
            QMessageBox.information(self, "反馈提交", "感谢您的反馈！我们会尽快处理。")
            self.feedback_edit.clear()
        else:
            QMessageBox.warning(self, "反馈提交", "请输入反馈内容。")

    def on_search_clicked(self):
        """查询按钮点击事件"""
        self.resultTable.setRowCount(0)
        # 获取查询条件
        project_name = self.projectInput.text().strip()
        invoice_number = self.invoiceNumberInput.text().strip()
        start_date = self.startDate.date().toString("yyyy-MM-dd")
        end_date = self.endDate.date().toString("yyyy-MM-dd")
        min_amount = self.minAmountInput.text().strip()
        max_amount = self.maxAmountInput.text().strip()

        # 构建查询条件字典
        criteria = {
            'project_name': project_name,
            'invoice_number': invoice_number,
            'start_date': start_date,
            'end_date': end_date,
            'min_amount': float(min_amount) if min_amount else None,
            'max_amount': float(max_amount) if max_amount else None
        }

        try:
            # 调用后端查询方法获取原始数据
            results = backend.search_invoices(criteria)

            # 清空表格
            self.resultTable.setRowCount(0)

            # 填充表格数据
            for row, result in enumerate(results):
                self.resultTable.insertRow(row)
                for col, data in enumerate(result):
                    self.resultTable.setItem(row, col, QTableWidgetItem(str(data)))

                # 添加“查看”按钮
                view_button = QPushButton("查看")
                view_button.clicked.connect(lambda checked, invoice_id=result[0]: self.show_invoice_image(invoice_id))
                self.resultTable.setCellWidget(row, 5, view_button)

        except Exception as e:
            print(f"查询失败: {e}")
            QMessageBox.critical(self, "错误", f"查询过程中发生错误：{str(e)}")
    def update_search_table(self, data):
        self.resultTable.setRowCount(0)
        for row_data in data:
            row = self.resultTable.rowCount()
            self.resultTable.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                self.resultTable.setItem(row, col, item)

    def on_invoice_row_clicked(self, row, column):
        """当用户点击查询结果表格中的一行时触发此函数"""
        invoice_id_item = self.resultTable.item(row, 0)  # 假设第一列是 ID
        if invoice_id_item:
            invoice_id = invoice_id_item.text()
            img_data = backend.get_invoice_file(invoice_id)  # 调用后端方法获取图片
            if img_data:
                pixmap = QPixmap()  # 使用从 PyQt6.QtGui 导入的 QPixmap
                pixmap.loadFromData(img_data)
                self.imagePreviewLabel.setPixmap(pixmap.scaledToWidth(300))  # 缩放显示
            else:
                self.imagePreviewLabel.setText("无法加载图片")

    def show_invoice_image(self, invoice_id):
        image_data = backend.get_invoice_file(invoice_id)
        if not image_data:
            QMessageBox.warning(self, "警告", "无法加载发票文件")
            return

        # 尝试将图片数据保存到本地文件
        temp_file_path = f"temp_invoice_{invoice_id}.jpg"
        try:
            with open(temp_file_path, "wb") as f:
                f.write(image_data)
            print(f"图片已保存到 {temp_file_path}")
            # 使用系统默认程序打开图片
            os.startfile(temp_file_path)
        except Exception as e:
            print(f"保存或打开图片时出错: {e}")
            QMessageBox.warning(self, "警告", f"保存或打开图片时出错: {e}")

    def clear_preview_on_page_change(self):
        # 清空预览区域
        self.imagePreviewLabel.clear()
        self.imagePreviewLabel.setText("图片预览区域")



# 启动应用
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InvoiceApp()
    window.show()
    sys.exit(app.exec())

