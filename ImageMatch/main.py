import sys
import os
import random
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QFileDialog, QHBoxLayout, QVBoxLayout, QListWidget, QMessageBox, QSizePolicy, QSplitter, QListView)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint, QSize

from match_canvas import MatchCanvas
import generate_rt_gt


class MatchAnnotator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('图像匹配标注软件')
        self.resize(1600, 900)  # 适合大部分显示器
        self.case_dir = ''
        self.img_names = []
        self.left_idx = 0
        self.right_idx = 1

        self.match_data = []  # [{"name": [name1, name2], matches:[[[x1,y1],[x2,y2]], ...]}, ...]
        self.pnp_gt = {}

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        splitter = QSplitter()

        # 左侧：已完成matches列表
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.match_list = QListWidget()
        self.match_list.clicked.connect(self.select_match_file)
        left_layout.addWidget(QLabel('已完成的匹配对'))
        left_layout.addWidget(self.match_list)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # 右侧：原有主界面
        right_widget = QWidget()
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton('打开数据集文件夹')
        self.btn_open.clicked.connect(self.open_folder)
        btn_layout.addWidget(self.btn_open)
        self.btn_add_match_data = QPushButton('添加匹配数据')
        self.btn_add_match_data.clicked.connect(self.add_match_data)
        btn_layout.addWidget(self.btn_add_match_data)
        self.btn_compute_pnp = QPushButton('计算PnP误差')
        self.btn_compute_pnp.clicked.connect(self.compute_pnp_error)
        btn_layout.addWidget(self.btn_compute_pnp)
        self.btn_save = QPushButton('保存匹配点')
        self.btn_save.clicked.connect(self.save_matches)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        img_select_layout = QHBoxLayout()
        self.left_list = QListWidget()
        self.left_list.clicked.connect(self.select_left_img)
        img_select_layout.addWidget(self.left_list)
        self.right_list = QListWidget()
        self.right_list.clicked.connect(self.select_right_img)
        img_select_layout.addWidget(self.right_list)
        layout.addLayout(img_select_layout)

        self.canvas = MatchCanvas(self)
        layout.addWidget(self.canvas, stretch=1)
        right_widget.setLayout(layout)
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 1400])
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    # 
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择数据集文件夹')
        if folder:
            img_dir = os.path.join(folder, 'img')
            if not os.path.exists(img_dir):
                QMessageBox.warning(self, '错误', '未找到img文件夹')
                return
            self.case_dir = folder

            # img
            self.img_names = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))]
            self.img_names.sort()
            self.left_list.clear()
            self.right_list.clear()
            self.left_list.addItems(self.img_names)
            self.right_list.addItems(self.img_names)
            if len(self.img_names) >= 2:
                self.left_idx = 0
                self.right_idx = 1
                self.left_list.setCurrentRow(self.left_idx)
                self.right_list.setCurrentRow(self.right_idx)
                self.show_images()
            
            # match
            match_data_path = os.path.join(self.case_dir, "matches.json")
            if os.path.exists(match_data_path):
                with open(match_data_path, "r") as f:
                    self.match_data = json.load(f)
            
            # pnp_gt
            pnp_gt_path = os.path.join(self.case_dir, "pnp_gt.json")
            if os.path.exists(pnp_gt_path):
                with open(pnp_gt_path, "r") as f:
                    self.pnp_gt = json.load(f)

            # 刷新matches文件列表
            self.refresh_match_list()

    def add_match_data(self):
        self.generate_match_data()
        self.refresh_match_list()
    
    def compute_pnp_error(self):
        self.generate_match_data()
        self.pnp_gt = generate_rt_gt.run(self.match_data, self.case_dir)
        self.refresh_match_list()
    
    def save_matches(self):
        with open(os.path.join(self.case_dir, 'matches.json'), 'w', encoding='utf-8') as f:
            json.dump(self.match_data, f, ensure_ascii=False, indent=2)
        
        pnp_gt_path = os.path.join(self.case_dir, "pnp_gt.json")
        with open(pnp_gt_path, "w") as f:
            json.dump(self.pnp_gt, f, indent=2)
        
        self.save_match_vis()

        QMessageBox.information(self, '保存成功', f'标注结果已保存到matches.json，可视化结果已保存到 match_vis 文件夹')
        
    # 
    def generate_match_data(self):
        left_points = self.canvas.get_left_points()
        right_points = self.canvas.get_right_points()
        if len(left_points) != len(right_points):
            QMessageBox.warning(self, '错误', '两张图像的特征点数量不一致')
            return
        if not left_points:
            QMessageBox.warning(self, '错误', '未标注特征点')
            return
    
        left_name = os.path.splitext(self.img_names[self.left_idx])[0]
        right_name = os.path.splitext(self.img_names[self.right_idx])[0]
        new_entry = {
            "name": [left_name, right_name],
            "matches": [
                [[pt1[0], pt1[1]], [pt2[0], pt2[1]]] for pt1, pt2 in zip(left_points, right_points)
            ]
        }
        # 更新或添加该图像对的标注
        updated = False
        for i, entry in enumerate(self.match_data):
            if entry.get('name') == new_entry['name']:
                self.match_data[i] = new_entry
                updated = True
                break
        if not updated:
            self.match_data.append(new_entry)

    def refresh_match_list(self):
        self.match_list.clear()

        match_info_list = []
        for data in self.match_data:
            name0, name1 = data['name'][0], data['name'][1]
            name_str = f"{name0}_{name1}"
            
            pnp_error = self.find_pnp_error(name0, name1)
            if pnp_error is not None:
                name_str += f" (PnP误差: {pnp_error:.2f})"

            match_info_list.append(name_str)

        self.match_list.addItems(match_info_list)

    def find_pnp_error(self, name0, name1):
        if "pnp_gt" in self.pnp_gt:
            for result in self.pnp_gt["pnp_gt"]:
                if name0==result["name"][0] and name1==result["name"][1]:
                    return result["pnp_error"]
        return None
    
    def save_match_vis(self):
        vis_dir = os.path.join(self.case_dir, 'match_vis')
        os.makedirs(vis_dir, exist_ok=True)

        for data in self.match_data:
            img0, img1 = data["name"][0], data["name"][1]
            img0_path = os.path.join(self.case_dir, 'img', img0 + '.png')
            img1_path = os.path.join(self.case_dir, 'img', img1 + '.png')

            left_img = QPixmap(img0_path)
            right_img = QPixmap(img1_path)
            w, h = left_img.width(), left_img.height()
            margin = 20
            canvas_w = w * 2 + margin
            canvas_h = h
            vis_pixmap = QPixmap(canvas_w, canvas_h)
            vis_pixmap.fill(QColor(255,255,255))
            painter = QPainter(vis_pixmap)
            painter.drawPixmap(0, 0, left_img)
            painter.drawPixmap(w + margin, 0, right_img)
            color_list = [QColor(255, 0, 0, 128), QColor(0, 255, 0, 128), QColor(0, 0, 255, 128), QColor(255, 255, 0, 128), QColor(255, 0, 255, 128), QColor(0, 255, 255, 128), QColor(128, 0, 128, 128), QColor(128, 128, 0, 128), QColor(0, 128, 128, 128), QColor(128, 0, 0, 128), QColor(0, 128, 0, 128), QColor(0, 0, 128, 128)]
            for i, pair in enumerate(data['matches']):
                color = color_list[i % len(color_list)]
                pen = QPen(color, 6)
                painter.setPen(pen)
                painter.drawPoint(QPoint(pair[0][0], pair[0][1]))
                painter.drawPoint(QPoint(pair[1][0] + w + margin, pair[1][1]))
                pen = QPen(color, 2)
                painter.setPen(pen)
                painter.drawLine(QPoint(pair[0][0], pair[0][1]), QPoint(pair[1][0] + w + margin, pair[1][1]))
            painter.end()
            vis_path = os.path.join(vis_dir, f'{img0}_{img1}.png')
            vis_pixmap.save(vis_path)
        
    def select_match_file(self):
        idx = self.match_list.currentRow()
        data = self.match_data[idx]

        # 自动切换左右图片
        self.left_idx = self.img_names.index(data["name"][0] + '.png')
        self.right_idx =  self.img_names.index(data["name"][1] + '.png')

        self.left_list.setCurrentRow(self.left_idx)
        self.right_list.setCurrentRow(self.right_idx)
        self.show_images()
        # 读取点对
        matches = []
        for pair in data['matches']:
            if len(pair) == 2:
                matches.append({'left': tuple(pair[0]), 'right': tuple(pair[1])})
        self.canvas.matches = matches
        self.canvas.update()

    def select_left_img(self):
        self.left_idx = self.left_list.currentRow()
        self.show_images()

    def select_right_img(self):
        self.right_idx = self.right_list.currentRow()
        self.show_images()

    def show_images(self):
        if self.case_dir and self.img_names:
            img_dir = os.path.join(self.case_dir, 'img')
            left_img = os.path.join(img_dir, self.img_names[self.left_idx])
            right_img = os.path.join(img_dir, self.img_names[self.right_idx])
            self.canvas.set_images(left_img, right_img)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MatchAnnotator()
    window.show()
    sys.exit(app.exec_())
