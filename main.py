from PyQt6.QtWidgets import QApplication
from front import InvoiceApp
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InvoiceApp()
    window.show()
    sys.exit(app.exec())
