import sys
import os
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import cv2
from paddleocr import PaddleOCR

class CopyrightPageRecognizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')

    def initUI(self):
        self.setWindowTitle('图书版权页识别系统')
        self.setGeometry(100, 100, 1200, 800)

        # 创建主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # 左侧布局（图片显示区域）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(600, 600)
        self.image_label.setStyleSheet('border: 1px solid black')
        left_layout.addWidget(self.image_label)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.upload_btn = QPushButton('上传图片')
        self.recognize_btn = QPushButton('识别版权页')
        self.recognize_btn.setEnabled(False)
        button_layout.addWidget(self.upload_btn)
        button_layout.addWidget(self.recognize_btn)
        left_layout.addLayout(button_layout)

        # 右侧布局（识别结果显示区域）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel('识别结果：'))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        right_layout.addWidget(self.result_text)

        # 添加左右布局到主布局
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        # 连接信号和槽
        self.upload_btn.clicked.connect(self.upload_image)
        self.recognize_btn.clicked.connect(self.recognize_copyright)

        self.image_path = None

    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择图片', '', 
                                                 'Images (*.png *.jpg *.jpeg *.bmp)')
        if file_name:
            self.image_path = file_name
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                         Qt.KeepAspectRatio, 
                                         Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.recognize_btn.setEnabled(True)

    def recognize_copyright(self):
        if not self.image_path:
            return

        try:
            # 使用PaddleOCR进行识别
            result = self.ocr.ocr(self.image_path, cls=True)
            if not result or not result[0]:
                QMessageBox.warning(self, '警告', '未能识别到文字信息！')
                return

            # 提取识别结果
            text_results = []
            for line in result[0]:
                text = line[1][0]  # 获取识别的文本
                text_results.append(text)

            # 解析版权信息
            copyright_info = self.parse_copyright_info(text_results)
            
            # 显示结果
            self.display_results(copyright_info)

        except Exception as e:
            QMessageBox.critical(self, '错误', f'识别过程中出现错误：{str(e)}')

    def parse_copyright_info(self, text_results):
        copyright_info = {
            'ISBN': '',
            '书名': '',
            '作者': '',
            '出版社': '',
            '出版时间': '',
            '版次': '',
            '印次': '',
            '定价': '',
            '开本': '',
            '印张': '',
            '字数': '',
            'CIP编号': '',
            '中图分类号': ''
        }

        # 合并所有文本
        full_text = '\n'.join(text_results)

        # 解析ISBN
        isbn_pattern = r'ISBN\s*[0-9-]{13,17}'
        isbn_match = re.search(isbn_pattern, full_text)
        if isbn_match:
            copyright_info['ISBN'] = isbn_match.group(0)

        # 解析CIP编号
        cip_num_pattern = r'CIP\s*数据核字\s*\([0-9]{4}\)\s*第\s*[0-9-]*\s*号'
        cip_num_match = re.search(cip_num_pattern, full_text)
        if cip_num_match:
            copyright_info['CIP编号'] = cip_num_match.group(0)

        # 解析中图分类号
        for line in text_results:
            if 'IV' in line:
                class_match = re.search(r'IV[0-9.A-Z]+', line)
                if class_match:
                    copyright_info['中图分类号'] = class_match.group(0)

        # 解析其他信息
        for line in text_results:
            # 解析包含出版信息的行
            if '/' in line and '：' in line and ('出版社' in line or '出版' in line):
                parts = line.split('/')
                if len(parts) >= 2:
                    # 提取书名
                    copyright_info['书名'] = parts[0].split('：')[-1].strip()
                    # 提取作者和出版信息
                    pub_info = parts[1].strip()
                    # 提取作者
                    if '主编' in pub_info or '著' in pub_info or '编' in pub_info:
                        author_end = pub_info.find('主编')
                        if author_end == -1:
                            author_end = pub_info.find('著')
                        if author_end == -1:
                            author_end = pub_info.find('编')
                        if author_end != -1:
                            copyright_info['作者'] = pub_info[:author_end+2].strip()
                    # 提取出版社和时间
                    if '：' in pub_info:
                        pub_parts = pub_info.split('：')
                        if len(pub_parts) >= 2:
                            # 提取出版社
                            pub_house = pub_parts[1].split('，')[0].strip()
                            copyright_info['出版社'] = pub_house
                            # 提取出版时间
                            if '，' in pub_parts[1]:
                                pub_date = pub_parts[1].split('，')[1].strip()
                                copyright_info['出版时间'] = pub_date

            # 版次信息
            elif '版' in line and '年' in line and '月' in line:
                version_match = re.search(r'(\d{4})年(\d{1,2})月第(\d+)版', line)
                if version_match and not copyright_info['版次']:
                    copyright_info['版次'] = version_match.group(0)

            # 印次信息
            elif '印' in line and '年' in line and '月' in line:
                print_match = re.search(r'(\d{4})年(\d{1,2})月第(\d+)次印刷', line)
                if print_match and not copyright_info['印次']:
                    copyright_info['印次'] = print_match.group(0)

            # 定价信息
            elif '定价' in line or ('元' in line and any(c.isdigit() for c in line)):
                if not copyright_info['定价'] and '印张' not in line:
                    price_match = re.search(r'\d+\.?\d*元', line)
                    if price_match:
                        copyright_info['定价'] = price_match.group(0)

            # 开本信息
            elif '开本' in line or ('×' in line and '/' in line):
                format_match = re.search(r'\d+\s*×\s*\d+\s*1/\d+', line)
                if format_match and not copyright_info['开本']:
                    copyright_info['开本'] = format_match.group(0)

            # 印张信息
            elif '印张' in line or ('印张' in line and ':' in line):
                sheets_match = re.search(r'印张[：:]*\s*(\d+)', line)
                if sheets_match and not copyright_info['印张']:
                    copyright_info['印张'] = sheets_match.group(1)

            # 字数信息
            elif '字数' in line or ('千字' in line):
                words_match = re.search(r'字数[：:]*\s*(\d+)千?字', line)
                if words_match and not copyright_info['字数']:
                    copyright_info['字数'] = words_match.group(1) + '千字'

        return copyright_info

    def display_results(self, copyright_info):
        result_text = '版权页信息提取结果：\n\n'
        for key, value in copyright_info.items():
            result_text += f'{key}：{value}\n'
        self.result_text.setText(result_text)

def main():
    app = QApplication(sys.argv)
    window = CopyrightPageRecognizer()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()