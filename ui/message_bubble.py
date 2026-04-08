import re
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from paths import get_asset_path

class MessageBubble(QWidget):
    """
    单个消息气泡组件

    用于在聊天界面中显示用户或AI消息，气泡样式根据发送者不同而不同
    """
    # 引用点击信号：携带citation索引
    citation_clicked = pyqtSignal(int)

    def __init__(self, message, is_user=True, citations=None, parent=None):
        """
        初始化消息气泡

        Args:
            message (str): 消息内容
            is_user (bool): 是否为用户消息，True为用户消息，False为AI消息
            citations (list): 引用定位信息列表（仅AI消息使用）
            parent: 父组件
        """
        super().__init__(parent)
        self.is_user = is_user
        self.message = message
        self.citations = citations or []
        self.init_ui()

    def init_ui(self):
        """初始化气泡UI"""
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        if self.is_user:
            self.setup_user_bubble(main_layout)
        else:
            self.setup_ai_bubble(main_layout)

    def setup_user_bubble(self, layout):
        """
        设置用户消息气泡

        Args:
            layout: 要添加气泡的布局
        """
        # 用户消息靠右
        layout.addStretch(3)  # 左侧弹性空间

        # 创建气泡及容器
        bubble_container, bubble = self.create_bubble(
            self.message,
            "userBubble",
            "#DCF8C6",  # 背景色
            "#B0F2B6",  # 边框色
            "#2C3E50",  # 文字色
            "15px 15px 0 15px"  # 圆角
        )

        # 创建头像
        avatar = self.create_avatar("user_avatar.svg")

        # 添加到布局
        layout.addWidget(bubble_container, 7)
        layout.addWidget(avatar)

        # 设置头像顶部对齐
        layout.setAlignment(avatar, Qt.AlignmentFlag.AlignTop)

    def setup_ai_bubble(self, layout):
        """
        设置AI消息气泡

        Args:
            layout: 要添加气泡的布局
        """
        # AI消息靠左
        # 创建头像
        avatar = self.create_avatar("ai_avatar.svg")

        # 创建气泡及容器
        bubble_container, bubble = self.create_bubble(
            self.message,
            "aiBubble",
            "#E3F2FD",  # 背景色
            "#BBDEFB",  # 边框色
            "#1A237E",  # 文字色
            "15px 15px 15px 0"  # 圆角
        )

        # 添加到布局
        layout.addWidget(avatar)
        layout.addWidget(bubble_container, 7)
        layout.addStretch(3)  # 右侧弹性空间

        # 设置头像顶部对齐
        layout.setAlignment(avatar, Qt.AlignmentFlag.AlignTop)

    def _convert_citations_to_html(self, text):
        """
        将文本中的 *ref-[N] 标记转换为可点击的 citation pill HTML

        Args:
            text: 包含 *ref-[N] 标记的文本

        Returns:
            str: 转换后的 HTML 文本
        """
        if not self.citations:
            # 没有citations数据，移除所有 *ref-[N] 标记
            return re.sub(r'\s*\*ref-\[\d+\]', '', text)

        def replace_ref(match):
            idx = int(match.group(1))
            if 0 <= idx < len(self.citations):
                label = self.citations[idx].get('label', f'§{idx}')
                # 截断过长的标签
                if len(label) > 20:
                    label = label[:18] + '...'
                return (
                    f' <a href="citation://{idx}" style="'
                    f'background-color: #E8EAF6; '
                    f'border: 1px solid #9FA8DA; '
                    f'border-radius: 8px; '
                    f'padding: 1px 6px; '
                    f'color: #283593; '
                    f'font-size: 12px; '
                    f'text-decoration: none;'
                    f'">[{label}]</a>'
                )
            return match.group(0)

        return re.sub(r'\*ref-\[(\d+)\]', replace_ref, text)

    def _prepare_display_text(self, text):
        """准备用于显示的文本，处理HTML转义和citation标记"""
        import html
        # 先HTML转义原始文本（防止注入）
        escaped = html.escape(text)
        # 然后转换citation标记为HTML链接
        return self._convert_citations_to_html(escaped)

    def create_bubble(self, message, object_name, bg_color, border_color, text_color, border_radius):
        """
        创建消息气泡

        Args:
            message: 消息内容
            object_name: 气泡的对象名称
            bg_color: 背景颜色
            border_color: 边框颜色
            text_color: 文本颜色
            border_radius: 边框圆角

        Returns:
            tuple: (气泡容器, 气泡)
        """
        # 创建气泡
        bubble = QFrame()
        bubble.setObjectName(object_name)
        bubble.setStyleSheet(f"""
            #{object_name} {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {border_radius};
                padding: 8px;
                min-width: 200px;
            }}
        """)

        # 气泡内布局
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(8, 8, 8, 8)

        # 消息文本
        msg_label = QLabel()
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {text_color}; font-size: 14px;")

        if not self.is_user and self.citations:
            # AI消息且有citations：使用富文本渲染citation pill
            msg_label.setTextFormat(Qt.TextFormat.RichText)
            msg_label.setOpenExternalLinks(False)
            display_html = self._prepare_display_text(message)
            msg_label.setText(display_html)
            msg_label.linkActivated.connect(self._on_link_clicked)
        else:
            # 用户消息或无citation的AI消息：纯文本
            msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if not self.is_user:
                # AI消息无citations时，清理可能残留的 *ref-[N] 标记
                message = re.sub(r'\s*\*ref-\[\d+\]', '', message)
            msg_label.setText(message)

        bubble_layout.addWidget(msg_label)

        # 创建容器（用于控制气泡大小比例）
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(bubble)
        container_layout.setStretch(0, 4)  # 让气泡占据更多空间

        return container, bubble

    def _on_link_clicked(self, url):
        """处理citation链接点击"""
        if url.startswith("citation://"):
            try:
                idx = int(url.replace("citation://", ""))
                self.citation_clicked.emit(idx)
            except ValueError:
                pass

    def create_avatar(self, avatar_filename):
        """
        创建头像标签

        Args:
            avatar_filename: 头像文件名

        Returns:
            QLabel: 包含头像的标签
        """
        avatar = QLabel()
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet("border-radius: 16px;")

        # 获取头像路径并加载
        avatar_path = get_asset_path(avatar_filename)
        avatar.setPixmap(QPixmap(avatar_path).scaled(
            32, 32,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        return avatar


class LoadingBubble(QWidget):
    """
    显示加载动画的气泡组件

    用于在等待AI响应时显示动画效果
    """
    def __init__(self, parent=None):
        """初始化加载气泡"""
        super().__init__(parent)

        # 设置布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建气泡框架
        bubble = QFrame()
        bubble.setObjectName("loadingBubble")
        bubble.setStyleSheet("""
            #loadingBubble {
                background-color: #E3F2FD;
                border: 1px solid #BBDEFB;
                border-radius: 15px 15px 15px 0;
                padding: 8px;
                min-width: 80px;
            }
        """)

        # 气泡内布局
        bubble_layout = QHBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 10, 10, 10)

        # 加载文本
        self.loading_label = QLabel("AI思考中")
        self.loading_label.setStyleSheet("color: #1A237E; font-size: 14px;")

        bubble_layout.addWidget(self.loading_label)
        layout.addWidget(bubble)
        layout.addStretch(1)

        # 设置动画计时器
        self.dots_count = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(500)  # 每500ms更新一次

    def update_animation(self):
        """更新加载动画文本"""
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.loading_label.setText(f"AI思考中{dots}")

    def stop_animation(self):
        """停止动画"""
        self.animation_timer.stop()
