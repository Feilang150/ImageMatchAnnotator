import os
import cv2
import sys
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore


class ImageSelector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Selector (Concatenated Playback)")
        self.resize(1500, 1000)

        # --- State ---
        self.root_dir = None
        self.save_dir = None
        self.video_files = []
        self.video_caps = []
        self.video_frame_counts = []
        self.video_fps = None
        self.total_frames_all = 0
        self.current_global_frame = 0
        self.current_video_index = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.split_enabled = False  # whether to split left/right on save

        # --- Layout ---
        layout = QtWidgets.QVBoxLayout()

        # Top row: folder select + split toggle
        top_layout = QtWidgets.QHBoxLayout()

        self.load_btn = QtWidgets.QPushButton("📂 选择文件夹")
        self.load_btn.setFixedHeight(36)
        self.load_btn.clicked.connect(self.load_folder)
        top_layout.addWidget(self.load_btn)

        self.split_checkbox = QtWidgets.QCheckBox("保存时分割左右")
        self.split_checkbox.stateChanged.connect(self.toggle_split)
        top_layout.addWidget(self.split_checkbox)

        self.rename_btn = QtWidgets.QPushButton("重命名图像文件")
        self.rename_btn.setFixedHeight(36)
        self.rename_btn.clicked.connect(self.rename_imgs)
        top_layout.addWidget(self.rename_btn)

        top_layout.addStretch(1)
        layout.addLayout(top_layout)

        # --- Video display ---
        self.label = QtWidgets.QLabel("请选择包含 MP4 视频的文件夹。")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("background-color: #222; border: 1px solid #888;")
        self.label.setMinimumSize(1200, 700)  # 放大视频窗口
        layout.addWidget(self.label, stretch=10)

        # --- Controls ---
        controls_layout = QtWidgets.QHBoxLayout()
        # 左侧：播放/暂停
        play_btn = QtWidgets.QPushButton("▶ 播放 / ⏸ 暂停")
        play_btn.setFixedWidth(120)
        play_btn.clicked.connect(self.toggle_play)
        controls_layout.addWidget(play_btn)

        # 中间：步进按钮
        step_layout = QtWidgets.QHBoxLayout()
        # 6个步进按钮，分别设置快捷键提示
        step_times = [(-5, "-5s [Q]"), (-1, "-1s [A]"), (-0.1, "-100ms [Z]"),
                      (0.1, "+100ms [X]"), (1, "+1s [S]"), (5, "+5s [W]")]
        for delta, label in step_times:
            btn = self.make_button(label, lambda _, d=delta: self.step_time(d))
            btn.setFixedWidth(70)
            step_layout.addWidget(btn)
        controls_layout.addLayout(step_layout)

        # 右侧：保存按钮
        save_btn = self.make_button("💾 保存帧", self.save_frame, "#4CAF50")
        save_btn.setFixedWidth(120)
        controls_layout.addWidget(save_btn)
        layout.addLayout(controls_layout)

        # --- Slider ---
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.valueChanged.connect(self.on_slider)
        self.slider.setEnabled(False)
        self.slider.setMinimumHeight(24)
        layout.addWidget(self.slider)

        # --- Time label ---
        self.time_label = QtWidgets.QLabel("0.00s / 0.00s")
        self.time_label.setAlignment(QtCore.Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(self.time_label)

        self.setLayout(layout)

        # --- 快捷键 ---
        QtWidgets.QShortcut(QtGui.QKeySequence("Return"), self, activated=self.save_frame)
        # 6个步进快捷键：Q/W/A/S/Z/X 分别对应 -5s/-1s/-100ms/+100ms/+1s/+5s
        self.step_shortcuts = [
            QtWidgets.QShortcut(QtGui.QKeySequence("Q"), self, activated=lambda: self.step_time(-5)),
            QtWidgets.QShortcut(QtGui.QKeySequence("A"), self, activated=lambda: self.step_time(-1)),
            QtWidgets.QShortcut(QtGui.QKeySequence("Z"), self, activated=lambda: self.step_time(-0.1)),
            QtWidgets.QShortcut(QtGui.QKeySequence("X"), self, activated=lambda: self.step_time(0.1)),
            QtWidgets.QShortcut(QtGui.QKeySequence("S"), self, activated=lambda: self.step_time(1)),
            QtWidgets.QShortcut(QtGui.QKeySequence("W"), self, activated=lambda: self.step_time(5)),
        ]

    # --- UI helper ---
    def make_button(self, text, func, color=None):
        btn = QtWidgets.QPushButton(text)
        btn.clicked.connect(func)
        if color:
            btn.setStyleSheet(f"background-color:{color}; color:white; font-weight:bold;")
        return btn

    # --- Core logic ---
    def load_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder with MP4 videos")
        if not folder:
            return
        self.root_dir = folder
        self.load_videos()
        self.update_frame()

    def load_videos(self):
        """Load all mp4s in folder, concatenate playback info."""
        self.video_files = sorted([f for f in os.listdir(self.root_dir) if f.lower().endswith(".mp4")])
        if not self.video_files:
            QtWidgets.QMessageBox.warning(self, "Error", "No MP4 files found in this folder.")
            return

        # Reset
        self.video_caps.clear()
        self.video_frame_counts.clear()
        self.video_fps = None
        self.total_frames_all = 0
        self.current_global_frame = 0

        for v in self.video_files:
            cap = cv2.VideoCapture(os.path.join(self.root_dir, v))
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {v}")
            fps = cap.get(cv2.CAP_PROP_FPS)
            if self.video_fps is None:
                self.video_fps = fps
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_caps.append(cap)
            self.video_frame_counts.append(count)
            self.total_frames_all += count

        self.slider.setEnabled(True)
        self.slider.setMaximum(self.total_frames_all - 1)

        # Prepare save folder
        self.save_dir = os.path.join(self.root_dir, "img")
        os.makedirs(self.save_dir, exist_ok=True)

    def toggle_split(self, state):
        self.split_enabled = bool(state)

    def get_video_by_global_frame(self, global_frame):
        accum = 0
        for i, count in enumerate(self.video_frame_counts):
            if global_frame < accum + count:
                local_frame = global_frame - accum
                return i, local_frame
            accum += count
        return len(self.video_frame_counts) - 1, self.video_frame_counts[-1] - 1

    def update_frame(self):
        if not self.video_caps:
            return
        idx, local_frame = self.get_video_by_global_frame(self.current_global_frame)
        self.current_video_index = idx
        cap = self.video_caps[idx]
        cap.set(cv2.CAP_PROP_POS_FRAMES, local_frame)
        ret, frame = cap.read()
        if not ret:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        if self.split_enabled:
            mid = w // 2
            left = frame[:, :mid]
            left_resized = cv2.resize(left, (w, h), interpolation=cv2.INTER_LINEAR)
            show_frame = left_resized
        else:
            show_frame = frame
        qt_img = QtGui.QImage(show_frame.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        qt_img = qt_img.scaled(960, 540, QtCore.Qt.KeepAspectRatio)
        self.label.setPixmap(QtGui.QPixmap.fromImage(qt_img))

        self.slider.blockSignals(True)
        self.slider.setValue(self.current_global_frame)
        self.slider.blockSignals(False)

        total_time = self.total_frames_all / self.video_fps
        current_time = self.current_global_frame / self.video_fps
        self.time_label.setText(f"{current_time:.2f}s / {total_time:.2f}s")

    def toggle_play(self):
        if not self.video_caps:
            return
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(int(1000 / self.video_fps))

    def next_frame(self):
        self.current_global_frame += 1
        if self.current_global_frame >= self.total_frames_all:
            self.current_global_frame = 0
        self.update_frame()

    def on_slider(self, value):
        self.current_global_frame = int(value)
        self.update_frame()

    def step_time(self, delta_sec):
        if not self.video_caps:
            return
        new_frame = self.current_global_frame + int(delta_sec * self.video_fps)
        new_frame = max(0, min(self.total_frames_all - 1, new_frame))
        self.current_global_frame = new_frame
        self.update_frame()

    def save_frame(self):
        if not self.video_caps:
            return
        idx, local_frame = self.get_video_by_global_frame(self.current_global_frame)
        cap = self.video_caps[idx]
        cap.set(cv2.CAP_PROP_POS_FRAMES, local_frame)
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to capture frame.")
            return

        video_name = os.path.splitext(self.video_files[idx])[0]
        t = local_frame / self.video_fps

        if not self.split_enabled:
            save_path = os.path.join(self.save_dir, f"{video_name}_{t:.3f}s.png")
            cv2.imwrite(save_path, frame)
            print(f"✅ Saved frame: {save_path}")
        else:
            h, w, _ = frame.shape
            mid = w // 2
            left = frame[:, :mid]
            left_resized = cv2.resize(left, (w, h), interpolation=cv2.INTER_LINEAR)
            left_path = os.path.join(self.save_dir, f"{video_name}_{t:.3f}s.png")
            cv2.imwrite(left_path, left_resized)
            print(f"✅ Saved split: {left_path}")

    def wheelEvent(self, event):
        if not self.video_caps:
            return
        delta = event.angleDelta().y()
        # 每次滚动步进100ms
        step = int(0.1 * self.video_fps)
        if delta > 0:
            self.current_global_frame = min(self.total_frames_all - 1, self.current_global_frame + step)
        else:
            self.current_global_frame = max(0, self.current_global_frame - step)
        self.update_frame()
    
    def rename_imgs(self):
        """
        Rename all files in the given folder sequentially (0, 1, 2, ...),
        sorted by their current file names. Original extensions are preserved.
        """
        if (self.save_dir is None) or (not os.path.isdir(self.save_dir)):
            print(f"Error: Folder not found - {self.save_dir}")
            return
    
        # List and sort all files (ignore directories)
        files = [f for f in os.listdir(self.save_dir) if os.path.isfile(os.path.join(self.save_dir, f))]
        files.sort()

        # Rename each file
        for i, filename in enumerate(files):
            old_path = os.path.join(self.save_dir, filename)
            ext = os.path.splitext(filename)[1]  # keep original extension
            new_name = f"{i}{ext}"
            new_path = os.path.join(self.save_dir, new_name)

            if not os.path.exists(new_path):
                os.rename(old_path, new_path)
                print(f"Renamed: {filename} -> {new_name}")
            else:
                print(f"Skipped (already exists): {new_name}")

        print("✅ All files renamed successfully.")



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    selector = ImageSelector()
    selector.show()
    sys.exit(app.exec_())
