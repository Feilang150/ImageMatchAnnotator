# ImageMatchAnnotator

图像匹配标注与配准工具集，包含图像匹配标注、视频帧提取、图像配准三大功能模块。

## 项目结构

```
ImageMatchAnnotator/
├── ImageMatch/           # 图像匹配标注工具
│   ├── main.py           # 主程序入口
│   ├── match_canvas.py   # 画布组件（支持放大镜）
│   ├── generate_rt_gt.py # 生成旋转平移真值
│   └── pnp.py            # PnP算法实现
├── ImageSelector/        # 视频帧提取工具
│   └── main.py           # 主程序入口
├── Registration/         # 图像配准模块
│   ├── main.py           # 主程序
│   ├── Ui_win.py         # UI定义
│   ├── win.ui            # Qt Designer文件
│   └── vtkWidget/        # VTK 3D可视化组件
├── requirements.txt     # Python依赖
└── LICENSE               # 许可证
```

## 功能模块

### 1. ImageMatch - 图像匹配标注

用于标注图像对之间的匹配点，并计算PnP重投影误差。

**功能特性：**
- 左右双图拼接显示，自动缩放适配窗口
- 鼠标左键点击添加匹配点，右键删除
- 放大镜功能辅助精确标注
- 自动匹配左右图像对应点
- 计算PnP重投影误差
- 导出匹配可视化结果

**使用方法：**
```bash
cd ImageMatch
python main.py
```

**数据格式：**
- 数据集文件夹结构：
  ```
  case_dir/
  ├── img/           # 图像文件夹
  │   ├── 0.png
  │   ├── 1.png
  │   └── ...
  ├── matches.json   # 匹配点数据（自动生成）
  └── pnp_gt.json    # PnP真值（自动生成）
  ```

### 2. ImageSelector - 视频帧提取

从MP4视频中提取图像帧，支持连续播放和精确步进。

**功能特性：**
- 支持多个MP4视频串联播放
- 播放控制：播放/暂停、进度条拖拽
- 精确步进：支持 ±5s, ±1s, ±100ms 调整
- 快捷键支持（Q/W/A/S/Z/X）
- 可选左右分割保存
- 帧重命名工具

**使用方法：**
```bash
cd ImageSelector
python main.py
```

### 3. Registration - 图像配准

结合2D图像与3D模型的配准工具。

**功能特性：**
- VTK 3D模型显示
- 相机内参标定
- 世界坐标点计算
- 帧序列导航

**使用方法：**
```bash
cd Registration
# Windows
generate_exe.bat
# Linux
./generate_exe.sh
```

## 安装依赖

```bash
pip install -r requirements.txt
```

**依赖列表：**
- PyQt5
- numpy
- opencv-python
- vtk
- pyqtwebengine <5.16
- SimpleITK
- tqdm

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。
