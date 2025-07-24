# InvoiceManagementSystem
发票管理系统：主要还是用python搭建的，在我的项目里面主要分为了front（前段）、backend（后端）、sql（针对数据库连接）、main（将三个部分连接起来运行的文件），主要功能是可以上传发票图片，自动识别相关信息，如果有异常还可以手动输入修改，后面可以按照筛选要求筛选相关发票，并查看发票原件，还可以统计相应筛选条件下的发票总金额等数据
1.前端（front.py）：
PyQt6：构建图形界面，包括按钮、表格、输入框等。
QInputDialog：用于弹出窗口让用户手动输入项目名。
QTableWidget/QPushButton：实现发票数据展示和查看按钮功能。
(1)主要功能：
    文件上传（发票图片/PDF）
    显示OCR提取结果，并允许手动修改
    提交数据到数据库
    查询发票记录，并在表格中显示
    查看原始发票图片（通过点击“查看”按钮）
(2)与后端的连接方式：
  通过调用 backend.py 中的：process_invoice_image(file_path) → 提取OCR数据
                          insert_invoice(data, file_data) → 插入数据库
                          search_invoices(criteria) → 查询发票信息
                          get_invoice_file(invoice_id) → 获取图片二进制并保存为本地图片以供查看
2.后端（backend.py）
OCR识别：Tesseract OCR（pytesseract）
图像处理：OpenCV + Pillow
PDF转图片：pdf2image
uuid：生成发票唯一ID
(1)功能分为几个模块：
|OCR提取流程：
    支持图片 + PDF 文件识别
    清理 ICC 配置 + 图像压缩
    自动提取发票号、金额、日期、项目名
    项目名不识别时支持手动输入
|数据库操作调用：调用 sql.py 中的方法来插入、查询发票
|查询支持：基于多个字段筛选（发票号、日期范围、金额范围、项目名）
|文件获取模块：通过发票ID获取发票图片数据，供前端展示
3.数据库（sql.py / MySQL）
连接数据库： connect_db()
插入发票数据： insert_invoice(record, file_data)
查询全部发票： search_invoices()
按条件查询： search_invoices_by_criteria(...)
根据ID获取图片： get_invoice_file(invoice_id)
4.连接关系图
用户点击上传图片 → 前端调用 backend.process_invoice_image()
                   ↓
           OCR识别 + 字段提取
                   ↓
    前端确认数据 → backend.insert_invoice()
                   ↓
             backend → sql.insert_invoice() → MySQL

查询时：
用户点击查询 → 前端调用 backend.search_invoices(criteria)
                    ↓
       backend → sql.search_invoices_by_criteria()
                    ↓
                返回结果列表 → 前端表格更新显示

点击查看原图 → 调用 backend.get_invoice_file(invoice_id)
                    ↓
           backend → sql.get_invoice_file() → 返回图片二进制
                    ↓
      写入本地 & 显示图片
