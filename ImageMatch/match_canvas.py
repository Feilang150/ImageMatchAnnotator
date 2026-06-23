from PyQt5.QtWidgets import  QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal


class MatchCanvas(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.left_img = None
        self.right_img = None
        self.matches = []  # 每个元素为 {'left': (x, y), 'right': (x, y)}
        self.selected = None  # (side, idx)
        self.margin = 20  # 图像间距
        self.img_size = (0, 0)
        self.scale = 1.0
        self.setMouseTracking(True)
        self.setMinimumSize(800, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 放大镜相关设置
        self.mouse_pos = None             # 当前鼠标位置（widget坐标），无鼠标时为None
        self.mag_size = 180               # 放大镜在widget上显示的像素大小（正方形）
        self.mag_scale = 1.0            # 放大倍数（相对于原图像像素）
        self.mag_padding = 12             # 放大镜与鼠标之间的间距

    def set_images(self, left_path, right_path):
        self.left_img = QPixmap(left_path)
        self.right_img = QPixmap(right_path)
        self.img_size = (self.left_img.width(), self.left_img.height())
        self.matches = []
        self.selected = None
        self.update_scale()
        self.update()

    def update_scale(self):
        # 获取父窗口大小，计算缩放比例
        if self.img_size[0] == 0 or self.img_size[1] == 0:
            self.scale = 1.0
            return
        if self.parent() is not None:
            parent_size = self.parent().size()
            total_width = self.img_size[0] * 2 + self.margin
            total_height = self.img_size[1]
            if total_width == 0 or total_height == 0:
                self.scale = 1.0
                return
            scale_w = parent_size.width() / total_width
            scale_h = parent_size.height() / total_height
            self.scale = min(scale_w, scale_h, 1.0)
        else:
            self.scale = 1.0

    def resizeEvent(self, event):
        self.update_scale()
        self.update()
        super().resizeEvent(event)

    def sizeHint(self):
        w = int((self.img_size[0] * 2 + self.margin) * self.scale)
        h = int(self.img_size[1] * self.scale)
        return QSize(w, h)

    def mousePressEvent(self, event):
        x, y = event.pos().x(), event.pos().y()
        w, h = self.img_size
        s = self.scale
        # 左图
        if 0 <= x < w * s and 0 <= y < h * s:
            if event.button() == Qt.LeftButton:
                # 优先与未配对的右图点匹配
                for match in self.matches:
                    if match.get('left') is None and match.get('right') is not None:
                        match['left'] = (int(x / s), int(y / s))
                        self.update()
                        return
                # 否则新建一个左图点
                self.matches.append({'left': (int(x / s), int(y / s)), 'right': None})
            elif event.button() == Qt.RightButton:
                idx = self.find_match_index('left', int(x / s), int(y / s))
                if idx is not None:
                    self.matches[idx]['left'] = None
        # 右图
        elif w * s + self.margin <= x < (2 * w) * s + self.margin and 0 <= y < h * s:
            rx = int((x - w * s - self.margin) / s)
            if event.button() == Qt.LeftButton:
                # 优先与未配对的左图点匹配
                for match in self.matches:
                    if match.get('right') is None and match.get('left') is not None:
                        match['right'] = (rx, int(y / s))
                        self.update()
                        return
                # 否则新建一个右图点
                self.matches.append({'left': None, 'right': (rx, int(y / s))})
            elif event.button() == Qt.RightButton:
                idx = self.find_match_index('right', rx, int(y / s))
                if idx is not None:
                    self.matches[idx]['right'] = None
        self.update()

    def find_match_index(self, side, x, y, radius=10):
        for i, match in enumerate(self.matches):
            pt = match.get(side)
            if pt and (pt[0] - x) ** 2 + (pt[1] - y) ** 2 < radius ** 2:
                return i
        return None

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.left_img and self.right_img:
            painter = QPainter(self)
            w, h = self.img_size
            s = self.scale
            # draw left
            painter.drawPixmap(0, 0, self.left_img.scaled(int(w * s), int(h * s), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            # draw right
            painter.drawPixmap(int(w * s) + self.margin, 0, self.right_img.scaled(int(w * s), int(h * s), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            # draw all points and lines
            color_list = self.get_color_list(len(self.matches))
            for i, match in enumerate(self.matches):
                color = color_list[i]
                pen = QPen(color, 6)
                painter.setPen(pen)
                if match.get('left'):
                    painter.drawPoint(QPoint(int(match['left'][0] * s), int(match['left'][1] * s)))
                if match.get('right'):
                    painter.drawPoint(QPoint(int(match['right'][0] * s) + int(w * s) + self.margin, int(match['right'][1] * s)))
                if match.get('left') and match.get('right'):
                    pen = QPen(color, 2)
                    painter.setPen(pen)
                    painter.drawLine(QPoint(int(match['left'][0] * s), int(match['left'][1] * s)),
                                     QPoint(int(match['right'][0] * s) + int(w * s) + self.margin, int(match['right'][1] * s)))

            # 放大镜绘制（如果鼠标在图片上）
            if self.mouse_pos is not None:
                mx, my = self.mouse_pos.x(), self.mouse_pos.y()
                # 判断鼠标在哪一张图上，并选取对应原始图像与原图坐标
                src_pixmap = None
                src_x = src_y = None
                left_area_w = int(w * s)
                left_area_h = int(h * s)
                right_area_x = left_area_w + self.margin
                # 左图区域
                if 0 <= mx < left_area_w and 0 <= my < left_area_h:
                    src_pixmap = self.left_img
                    src_x = int(mx / s)
                    src_y = int(my / s)
                # 右图区域
                elif right_area_x <= mx < right_area_x + left_area_w and 0 <= my < left_area_h:
                    src_pixmap = self.right_img
                    src_x = int((mx - right_area_x) / s)
                    src_y = int(my / s)

                if src_pixmap is not None:
                    # 从原始pixmap中截取区域（以原始图像像素为单位），并放大到mag_size绘制
                    src_region_size = max(4, int(self.mag_size / self.mag_scale))
                    half = src_region_size // 2
                    img_w, img_h = src_pixmap.width(), src_pixmap.height()
                    x0 = max(0, min(img_w - src_region_size, src_x - half))
                    y0 = max(0, min(img_h - src_region_size, src_y - half))
                    src_rect = src_pixmap.copy(x0, y0, src_region_size, src_region_size)
                    if not src_rect.isNull():
                        mag_pix = src_rect.scaled(self.mag_size, self.mag_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                        # 放大镜要显示的位置（优先在鼠标右下方，若超出边界则调整）
                        draw_x = mx + self.mag_padding
                        draw_y = my + self.mag_padding
                        if draw_x + self.mag_size > self.width():
                            draw_x = mx - self.mag_padding - self.mag_size
                        if draw_y + self.mag_size > self.height():
                            draw_y = my - self.mag_padding - self.mag_size
                        # 背景和边框
                        radius = 6
                        painter.save()
                        painter.setRenderHint(QPainter.Antialiasing, True)
                        bg_color = QColor(255, 255, 255, 230)
                        painter.setBrush(bg_color)
                        pen = QPen(QColor(80, 80, 80, 200), 2)
                        painter.setPen(pen)
                        painter.drawRoundedRect(draw_x - 4, draw_y - 4, self.mag_size + 8, self.mag_size + 8, radius, radius)
                        # 绘制放大图
                        painter.drawPixmap(draw_x, draw_y, mag_pix)
                        # 中心十字线指示
                        cx = draw_x + self.mag_size // 2
                        cy = draw_y + self.mag_size // 2
                        cross_pen = QPen(QColor(255, 255, 255, 200), 1)
                        painter.setPen(cross_pen)
                        painter.drawLine(cx - 10, cy, cx + 10, cy)
                        painter.drawLine(cx, cy - 10, cx, cy + 10)
                        painter.restore()

    def get_color_list(self, n):
        # 生成n种不同的半透明颜色，超出则循环使用base_colors
        base_colors = [
            QColor(255, 0, 0, 128), QColor(0, 255, 0, 128), QColor(0, 0, 255, 128),
            QColor(255, 255, 0, 128), QColor(255, 0, 255, 128), QColor(0, 255, 255, 128),
            QColor(128, 0, 128, 128), QColor(128, 128, 0, 128), QColor(0, 128, 128, 128),
            QColor(128, 0, 0, 128), QColor(0, 128, 0, 128), QColor(0, 0, 128, 128)
        ]
        colors = []
        for i in range(n):
            colors.append(base_colors[i % len(base_colors)])
        return colors

    def get_left_points(self):
        return [m['left'] for m in self.matches if m.get('left') and m.get('right')]

    def get_right_points(self):
        return [m['right'] for m in self.matches if m.get('left') and m.get('right')]

    # 新增：追踪鼠标位置以更新放大镜显示
    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.mouse_pos = None
        self.update()
        super().leaveEvent(event)