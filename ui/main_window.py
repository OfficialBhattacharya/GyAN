from PyQt5.QtWidgets import (
    QMainWindow, QMenu, QAction, QApplication, QMenuBar, QStatusBar,
    QMessageBox, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout,
    QTextEdit, QGroupBox, QSplitter, QListWidget, QListWidgetItem, QProgressBar,
    QScrollArea, QFrame, QGridLayout, QSpacerItem, QSizePolicy, QTabWidget
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSignal as Signal, Qt
from config import load_config, save_config
from scheduler import schedule_daily_email, get_scheduler_status
from ui.settings_dialog import SettingsDialog
from news_scraper import get_upsc_news, get_weekly_news, get_monthly_news, generate_upsc_questions
from email_manager import send_news_email
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsArticleWidget(QFrame):
    """Custom widget for displaying news articles in newspaper style"""
    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #fefefe;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #f8f8f8;
                border: 1px solid #a0a0a0;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Source and date
        source_label = QLabel(f"📰 {self.article['source']}")
        source_label.setStyleSheet("""
            color: #c0392b;
            font-family: 'Times New Roman', serif;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(source_label)
        
        # Title
        title_label = QLabel(self.article['title'])
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 14px;
            font-weight: bold;
            line-height: 1.3;
            margin: 5px 0;
        """)
        layout.addWidget(title_label)
        
        # Summary if available
        if self.article.get('summary'):
            summary_label = QLabel(self.article['summary'][:200] + "...")
            summary_label.setWordWrap(True)
            summary_label.setStyleSheet("""
                color: #34495e;
                font-family: 'Times New Roman', serif;
                font-size: 11px;
                line-height: 1.4;
                margin: 5px 0;
            """)
            layout.addWidget(summary_label)
        
        # Link
        if self.article.get('link'):
            link_label = QLabel(f"🔗 <a href='{self.article['link']}' style='color: #3498db; text-decoration: none;'>Read Full Article</a>")
            link_label.setOpenExternalLinks(True)
            link_label.setStyleSheet("""
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #7f8c8d;
                margin-top: 5px;
            """)
            layout.addWidget(link_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)

class TypewriterTextEdit(QTextEdit):
    """Custom text edit with typewriter styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f8f5f0;
                border: 2px solid #8b4513;
                border-radius: 5px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.6;
                color: #2c3e50;
            }
            QTextEdit:focus {
                border: 2px solid #c0392b;
                background-color: #fefcf8;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.scheduler = None
        self.last_news_items = []
        self.init_ui()
        self.start_scheduler()
        self.update_status_display()
        
        # Timer to update status every 30 seconds
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_display)
        self.status_timer.start(30000)  # 30 seconds
        
    def init_ui(self):
        self.setWindowTitle("📰 UPSC News Aggregator - Daily Herald")
        # Set window to larger size to accommodate header
        self.setGeometry(50, 50, 1500, 1000)
        self.setMinimumSize(1300, 900)
        
        # Set application stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QMenuBar {
                background-color: #2c3e50;
                color: white;
                font-family: 'Times New Roman', serif;
                font-size: 12px;
                padding: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
                margin: 2px;
            }
            QMenuBar::item:selected {
                background-color: #34495e;
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #34495e;
                color: white;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("📰 Ready to deliver the news...")
        
        # Create central widget with newspaper layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # Add spacing between header and content
        main_layout.setContentsMargins(5, 5, 5, 5)  # Add margins around the main layout
        
        # Newspaper header
        self.create_newspaper_header(main_layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Controls and Status
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Tabbed News content
        right_panel = self.create_tabbed_news_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% left, 70% right)
        content_splitter.setSizes([420, 980])
        
        main_layout.addWidget(content_splitter)
        central_widget.setLayout(main_layout)
        
        # Log initial message
        self.log_message("📰 UPSC News Aggregator started - Ready to serve today's news!")
        
    def create_newspaper_header(self, layout):
        """Create newspaper-style header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 5px;
                margin: 0px;
            }
        """)
        header_frame.setFixedHeight(120)  # Compact height
        header_frame.setMinimumHeight(120)  # Ensure minimum height
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)  # Minimal spacing
        header_layout.setContentsMargins(10, 10, 10, 10)  # Minimal margins
        
        # Main title - simple and clean
        title_label = QLabel("📰 THE UPSC DAILY HERALD")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #1a252f;
            font-family: 'Times New Roman', serif;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
            text-transform: uppercase;
        """)
        header_layout.addWidget(title_label)
        
        # Subtitle - compact
        subtitle_label = QLabel("Your Premier Source for UPSC Current Affairs & Government News")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 12px;
            font-style: italic;
        """)
        header_layout.addWidget(subtitle_label)
        
        # Date - simple
        date_label = QLabel(f"📅 {datetime.now().strftime('%A, %B %d, %Y').upper()}")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("""
            color: #c0392b;
            font-family: 'Times New Roman', serif;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(date_label)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
        
    def create_left_panel(self):
        """Create left control panel with typewriter styling"""
        left_widget = QWidget()
        left_widget.setMaximumWidth(400)
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-right: 2px solid #bdc3c7;
            }
        """)
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        # Control Center
        controls_group = QGroupBox("📋 CONTROL CENTER")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-family: 'Times New Roman', serif;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #8b4513;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                background-color: #f8f5f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        
        # Style for buttons
        button_style = """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e8e8e8, stop: 1 #d0d0d0);
                border: 2px solid #8b4513;
                border-radius: 6px;
                padding: 12px 20px;
                font-family: 'Times New Roman', serif;
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f0f0f0, stop: 1 #e0e0e0);
                border: 2px solid #c0392b;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #d0d0d0, stop: 1 #c0c0c0);
            }
        """
        
        settings_btn = QPushButton("⚙️ NEWSROOM SETTINGS")
        settings_btn.setStyleSheet(button_style)
        settings_btn.clicked.connect(self.show_settings)
        controls_layout.addWidget(settings_btn)
        
        test_btn = QPushButton("📰 FETCH LATEST NEWS")
        test_btn.setStyleSheet(button_style)
        test_btn.clicked.connect(self.test_news_fetch)
        controls_layout.addWidget(test_btn)
        
        email_test_btn = QPushButton("📧 TEST TELEGRAPH")
        email_test_btn.setStyleSheet(button_style)
        email_test_btn.clicked.connect(self.test_email)
        controls_layout.addWidget(email_test_btn)
        
        controls_group.setLayout(controls_layout)
        left_layout.addWidget(controls_group)
        
        # Status Telegraph
        status_group = QGroupBox("📡 STATUS TELEGRAPH")
        status_group.setStyleSheet(controls_group.styleSheet())
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Initializing news wire...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            padding: 15px;
            background-color: #f8f5f0;
            border: 1px solid #d0d0d0;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            line-height: 1.5;
            color: #2c3e50;
        """)
        status_layout.addWidget(self.status_label)
        
        self.scheduler_status_label = QLabel("Scheduler: Not started")
        self.scheduler_status_label.setStyleSheet("""
            padding: 10px;
            color: #7f8c8d;
            font-family: 'Courier New', monospace;
            font-size: 10px;
            background-color: #ecf0f1;
            border-radius: 3px;
        """)
        status_layout.addWidget(self.scheduler_status_label)
        
        status_group.setLayout(status_layout)
        left_layout.addWidget(status_group)
        
        # Activity Log
        log_group = QGroupBox("📜 NEWSROOM LOG")
        log_group.setStyleSheet(controls_group.styleSheet())
        log_layout = QVBoxLayout()
        
        self.log_display = TypewriterTextEdit()
        self.log_display.setMaximumHeight(250)
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        
        clear_log_btn = QPushButton("🗑️ CLEAR LOG")
        clear_log_btn.setStyleSheet(button_style)
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        left_layout.addWidget(log_group)
        
        # Add stretch to push everything to top
        left_layout.addStretch()
        
        left_widget.setLayout(left_layout)
        return left_widget
        
    def create_tabbed_news_panel(self):
        """Create right panel with tabbed news display"""
        right_widget = QWidget()
        right_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ecf0f1, stop: 1 #bdc3c7);
                border: 2px solid #95a5a6;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                padding: 12px 20px;
                margin-right: 2px;
                font-family: 'Times New Roman', serif;
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                color: white;
                border: 2px solid #2c3e50;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
            }
        """)
        
        # Create tabs
        self.create_today_tab()
        self.create_weekly_tab()
        self.create_monthly_tab()
        self.create_upsc_questions_tab()
        
        right_layout.addWidget(self.tab_widget)
        right_widget.setLayout(right_layout)
        return right_widget
        
    def create_default_news_message(self):
        """Create default message when no news is available"""
        default_frame = QFrame()
        default_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                padding: 40px;
                margin: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel("📰")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 48px;
            margin-bottom: 20px;
        """)
        layout.addWidget(icon_label)
        
        message_label = QLabel("No headlines available yet")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("""
            color: #7f8c8d;
            font-family: 'Times New Roman', serif;
            font-size: 16px;
            font-style: italic;
            margin-bottom: 10px;
        """)
        layout.addWidget(message_label)
        
        instruction_label = QLabel("Click 'FETCH LATEST NEWS' to get today's headlines")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("""
            color: #95a5a6;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        """)
        layout.addWidget(instruction_label)
        
        default_frame.setLayout(layout)
        self.news_layout.addWidget(default_frame, 0, 0, 1, 3)
        
    def create_today_tab(self):
        """Create today's news tab"""
        today_widget = QWidget()
        today_layout = QVBoxLayout()
        today_layout.setSpacing(10)
        today_layout.setContentsMargins(20, 20, 20, 20)
        
        # News section header
        news_header = QLabel("📰 TODAY'S HEADLINES")
        news_header.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            padding: 10px 0;
            border-bottom: 2px solid #c0392b;
            margin-bottom: 20px;
        """)
        today_layout.addWidget(news_header)
        
        # News scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 15px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 7px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)
        
        # News content widget
        self.news_content_widget = QWidget()
        self.news_layout = QGridLayout()
        self.news_layout.setSpacing(15)
        self.news_layout.setContentsMargins(10, 10, 10, 10)
        
        # Default message
        self.create_default_news_message()
        
        self.news_content_widget.setLayout(self.news_layout)
        scroll_area.setWidget(self.news_content_widget)
        
        today_layout.addWidget(scroll_area)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 REFRESH HEADLINES")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                border: 2px solid #2c3e50;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Times New Roman', serif;
                font-size: 14px;
                font-weight: bold;
                color: white;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5dade2, stop: 1 #3498db);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #21618c);
            }
        """)
        refresh_btn.clicked.connect(self.refresh_news_display)
        today_layout.addWidget(refresh_btn)
        
        today_widget.setLayout(today_layout)
        self.tab_widget.addTab(today_widget, "📰 TODAY'S NEWS")
        
    def create_weekly_tab(self):
        """Create weekly news tab with geographic filtering"""
        weekly_widget = QWidget()
        weekly_layout = QVBoxLayout()
        weekly_layout.setSpacing(15)
        weekly_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel("📅 LAST WEEK'S NEWS DIGEST")
        header_label.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            padding: 10px 0;
            border-bottom: 2px solid #c0392b;
            margin-bottom: 20px;
        """)
        weekly_layout.addWidget(header_label)
        
        # Geographic filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        button_style = """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e8e8e8, stop: 1 #d0d0d0);
                border: 2px solid #8b4513;
                border-radius: 6px;
                padding: 10px 15px;
                font-family: 'Times New Roman', serif;
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f0f0f0, stop: 1 #e0e0e0);
                border: 2px solid #c0392b;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #d0d0d0, stop: 1 #c0c0c0);
            }
        """
        
        all_btn = QPushButton("🌍 ALL")
        all_btn.setStyleSheet(button_style)
        all_btn.clicked.connect(lambda: self.load_weekly_news("all"))
        filter_layout.addWidget(all_btn)
        
        mh_btn = QPushButton("🏛️ MAHARASHTRA")
        mh_btn.setStyleSheet(button_style)
        mh_btn.clicked.connect(lambda: self.load_weekly_news("maharashtra"))
        filter_layout.addWidget(mh_btn)
        
        india_btn = QPushButton("🇮🇳 INDIA")
        india_btn.setStyleSheet(button_style)
        india_btn.clicked.connect(lambda: self.load_weekly_news("india"))
        filter_layout.addWidget(india_btn)
        
        world_btn = QPushButton("🌐 WORLD")
        world_btn.setStyleSheet(button_style)
        world_btn.clicked.connect(lambda: self.load_weekly_news("world"))
        filter_layout.addWidget(world_btn)
        
        filter_layout.addStretch()
        weekly_layout.addLayout(filter_layout)
        
        # Weekly news content
        self.weekly_scroll_area = QScrollArea()
        self.weekly_scroll_area.setWidgetResizable(True)
        self.weekly_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 15px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 7px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)
        
        self.weekly_content_widget = QWidget()
        self.weekly_layout = QVBoxLayout()
        self.weekly_layout.setSpacing(15)
        self.weekly_layout.setContentsMargins(10, 10, 10, 10)
        
        # Default message
        default_msg = QLabel("📅 Select a region above to view last week's news")
        default_msg.setAlignment(Qt.AlignCenter)
        default_msg.setStyleSheet("""
            color: #7f8c8d;
            font-family: 'Times New Roman', serif;
            font-size: 14px;
            font-style: italic;
            padding: 40px;
        """)
        self.weekly_layout.addWidget(default_msg)
        
        self.weekly_content_widget.setLayout(self.weekly_layout)
        self.weekly_scroll_area.setWidget(self.weekly_content_widget)
        
        weekly_layout.addWidget(self.weekly_scroll_area)
        
        weekly_widget.setLayout(weekly_layout)
        self.tab_widget.addTab(weekly_widget, "📅 WEEKLY DIGEST")
        
    def create_monthly_tab(self):
        """Create monthly top news tab"""
        monthly_widget = QWidget()
        monthly_layout = QVBoxLayout()
        monthly_layout.setSpacing(15)
        monthly_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel("📊 TOP MONTHLY NEWS")
        header_label.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            padding: 10px 0;
            border-bottom: 2px solid #c0392b;
            margin-bottom: 20px;
        """)
        monthly_layout.addWidget(header_label)
        
        # Monthly news content
        self.monthly_scroll_area = QScrollArea()
        self.monthly_scroll_area.setWidgetResizable(True)
        self.monthly_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 15px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 7px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)
        
        self.monthly_content_widget = QWidget()
        self.monthly_layout = QVBoxLayout()
        self.monthly_layout.setSpacing(15)
        self.monthly_layout.setContentsMargins(10, 10, 10, 10)
        
        self.monthly_content_widget.setLayout(self.monthly_layout)
        self.monthly_scroll_area.setWidget(self.monthly_content_widget)
        
        monthly_layout.addWidget(self.monthly_scroll_area)
        
        # Load monthly news button
        load_monthly_btn = QPushButton("📊 LOAD MONTHLY HIGHLIGHTS")
        load_monthly_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e74c3c, stop: 1 #c0392b);
                border: 2px solid #2c3e50;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Times New Roman', serif;
                font-size: 14px;
                font-weight: bold;
                color: white;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ec7063, stop: 1 #e74c3c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a93226);
            }
        """)
        load_monthly_btn.clicked.connect(self.load_monthly_news)
        monthly_layout.addWidget(load_monthly_btn)
        
        monthly_widget.setLayout(monthly_layout)
        self.tab_widget.addTab(monthly_widget, "📊 MONTHLY HIGHLIGHTS")
        
    def create_upsc_questions_tab(self):
        """Create UPSC questions tab"""
        upsc_widget = QWidget()
        upsc_layout = QVBoxLayout()
        upsc_layout.setSpacing(15)
        upsc_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel("🎓 UPSC PRACTICE QUESTIONS")
        header_label.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            padding: 10px 0;
            border-bottom: 2px solid #c0392b;
            margin-bottom: 20px;
        """)
        upsc_layout.addWidget(header_label)
        
        # UPSC questions content
        self.upsc_scroll_area = QScrollArea()
        self.upsc_scroll_area.setWidgetResizable(True)
        self.upsc_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 15px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 7px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)
        
        self.upsc_content_widget = QWidget()
        self.upsc_layout = QVBoxLayout()
        self.upsc_layout.setSpacing(15)
        self.upsc_layout.setContentsMargins(10, 10, 10, 10)
        
        self.upsc_content_widget.setLayout(self.upsc_layout)
        self.upsc_scroll_area.setWidget(self.upsc_content_widget)
        
        upsc_layout.addWidget(self.upsc_scroll_area)
        
        # Generate questions button
        generate_btn = QPushButton("🎓 GENERATE PRACTICE QUESTIONS")
        generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #9b59b6, stop: 1 #8e44ad);
                border: 2px solid #2c3e50;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Times New Roman', serif;
                font-size: 14px;
                font-weight: bold;
                color: white;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #bb8fce, stop: 1 #9b59b6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #8e44ad, stop: 1 #7d3c98);
            }
        """)
        generate_btn.clicked.connect(self.load_upsc_questions)
        upsc_layout.addWidget(generate_btn)
        
        upsc_widget.setLayout(upsc_layout)
        self.tab_widget.addTab(upsc_widget, "🎓 UPSC QUESTIONS")
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('📁 File')
        
        settings_action = QAction('⚙️ Settings', self)
        settings_action.setShortcut('Ctrl+S')
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('❌ Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('🔧 Tools')
        
        test_news_action = QAction('📰 Test News Fetch', self)
        test_news_action.triggered.connect(self.test_news_fetch)
        tools_menu.addAction(test_news_action)
        
        test_email_action = QAction('📧 Test Email', self)
        test_email_action.triggered.connect(self.test_email)
        tools_menu.addAction(test_email_action)
        
        # Help menu
        help_menu = menubar.addMenu('❓ Help')
        
        about_action = QAction('ℹ️ About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def log_message(self, message):
        """Add message to the activity log with typewriter effect"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_display.append(formatted_message)
        
        # Keep only last 100 lines
        if self.log_display.document().lineCount() > 100:
            cursor = self.log_display.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 1)
            cursor.removeSelectedText()
        
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_status_display(self):
        """Update the status display with current information"""
        try:
            # Update main status
            email_configured = bool(self.config.get('email') and self.config.get('smtp_username'))
            sources_count = len(self.config.get('sources', []))
            keywords_count = len(self.config.get('keywords', []))
            
            status_text = f"""📧 TELEGRAPH: {'✅ CONNECTED' if email_configured else '❌ DISCONNECTED'}
📰 NEWS SOURCES: {sources_count} ACTIVE
🔍 KEYWORDS: {keywords_count} CONFIGURED
⏰ SCHEDULE: {self.config.get('send_time', 'NOT SET')}
📊 LAST FETCH: {len(self.last_news_items)} ARTICLES FOUND
⚡ STATUS: OPERATIONAL"""
            
            self.status_label.setText(status_text)
            
            # Update scheduler status
            if self.scheduler:
                scheduler_status = get_scheduler_status(self.scheduler)
                if scheduler_status.get('status') == 'running':
                    jobs = scheduler_status.get('jobs', [])
                    if jobs:
                        next_run = jobs[0].get('next_run')
                        if next_run:
                            from datetime import datetime
                            next_run_dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
                            next_run_str = next_run_dt.strftime('%Y-%m-%d %H:%M:%S')
                            self.scheduler_status_label.setText(f"📅 SCHEDULER: RUNNING (NEXT: {next_run_str})")
                        else:
                            self.scheduler_status_label.setText("📅 SCHEDULER: RUNNING")
                    else:
                        self.scheduler_status_label.setText("📅 SCHEDULER: RUNNING (NO JOBS)")
                else:
                    self.scheduler_status_label.setText(f"❌ SCHEDULER: {scheduler_status.get('status', 'UNKNOWN').upper()}")
            else:
                self.scheduler_status_label.setText("❌ SCHEDULER: NOT RUNNING")
                
            # Update status bar
            self.status_bar.showMessage(f"📰 UPSC Daily Herald - Telegraph: {'CONNECTED' if email_configured else 'DISCONNECTED'} | Scheduler: {'RUNNING' if self.scheduler else 'STOPPED'} | Articles: {len(self.last_news_items)}")
            
        except Exception as e:
            logger.error(f"Error updating status display: {e}")
            
    def refresh_news_display(self):
        """Refresh the news items display in newspaper format"""
        # Clear existing news items
        for i in reversed(range(self.news_layout.count())):
            self.news_layout.itemAt(i).widget().setParent(None)
        
        if self.last_news_items:
            # Display news in grid format (3 columns)
            for idx, item in enumerate(self.last_news_items[:15]):  # Show first 15 items
                row = idx // 3
                col = idx % 3
                
                article_widget = NewsArticleWidget(item)
                self.news_layout.addWidget(article_widget, row, col)
                
            # Add stretch to fill remaining space
            self.news_layout.setRowStretch(self.news_layout.rowCount(), 1)
        else:
            self.create_default_news_message()
            
    def clear_log(self):
        """Clear the activity log"""
        self.log_display.clear()
        self.log_message("📜 Newsroom log cleared")
        
    def start_scheduler(self):
        """Start the news scheduler"""
        try:
            if self.scheduler:
                self.scheduler.shutdown()
            self.scheduler = schedule_daily_email(self.config)
            self.log_message("📅 News scheduler started - Telegraph system operational")
            logger.info("Scheduler started successfully")
        except Exception as e:
            self.log_message(f"❌ Failed to start scheduler: {e}")
            logger.error(f"Failed to start scheduler: {e}")
            
    def test_news_fetch(self):
        """Test news fetching functionality"""
        try:
            self.log_message("📰 Fetching latest headlines from news sources...")
            self.status_bar.showMessage("📡 Connecting to news wire services...")
            
            news_items = get_upsc_news(self.config)
            self.last_news_items = news_items
            
            if news_items:
                message = f"✅ Successfully fetched {len(news_items)} headlines from the wire"
                self.log_message(message)
                QMessageBox.information(self, "📰 News Fetch Successful", 
                                      f"Successfully retrieved {len(news_items)} articles from news sources.")
                self.refresh_news_display()
            else:
                message = "⚠️ No headlines found matching your keywords"
                self.log_message(message)
                QMessageBox.warning(self, "📰 No News Found", 
                                  "No articles found matching your configured keywords.")
                
            self.update_status_display()
            self.status_bar.showMessage("📰 Ready to deliver the news...")
                
        except Exception as e:
            error_msg = f"❌ News fetch failed: {e}"
            self.log_message(error_msg)
            logger.error(error_msg)
            QMessageBox.critical(self, "📰 News Fetch Failed", f"Error retrieving news: {str(e)}")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
    def test_email(self):
        """Test email functionality"""
        try:
            if not self.config.get('email') or not self.config.get('smtp_username'):
                QMessageBox.warning(self, "📧 Telegraph Not Configured", 
                                  "Please configure telegraph (email) settings first.")
                return
                
            self.log_message("📧 Testing telegraph system...")
            self.status_bar.showMessage("📡 Sending test message via telegraph...")
            
            # Use last fetched news or create test news
            test_news = self.last_news_items if self.last_news_items else [{
                'source': 'UPSC Daily Herald',
                'title': 'Telegraph System Test - All Systems Operational',
                'link': 'https://example.com'
            }]
            
            send_news_email(self.config, test_news)
            message = "✅ Test telegraph message sent successfully!"
            self.log_message(message)
            QMessageBox.information(self, "📧 Telegraph Test Successful", 
                                  "Test message delivered successfully via telegraph system.")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
        except Exception as e:
            error_msg = f"❌ Telegraph test failed: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "📧 Telegraph Test Failed", 
                               f"Telegraph system error: {str(e)}")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
        
    def show_settings(self):
        """Show settings dialog"""
        try:
            dialog = SettingsDialog(self.config, self)
            if dialog.exec_():
                old_config = self.config.copy()
                self.config = dialog.get_updated_config()
                save_config(self.config)
                
                # Restart scheduler if schedule settings changed
                if (old_config.get('send_time') != self.config.get('send_time') or
                    old_config.get('sources') != self.config.get('sources') or
                    old_config.get('keywords') != self.config.get('keywords')):
                    self.start_scheduler()
                    
                self.log_message("⚙️ Newsroom settings updated successfully")
                self.update_status_display()
                logger.info("Settings updated successfully")
                
        except Exception as e:
            error_msg = f"❌ Settings dialog error: {e}"
            self.log_message(error_msg)
            logger.error(error_msg)
            QMessageBox.critical(self, "⚙️ Settings Error", f"Failed to open settings: {e}")
            
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <div style="text-align: center; font-family: 'Times New Roman', serif;">
            <h2 style="color: #2c3e50;">📰 THE UPSC DAILY HERALD</h2>
            <p style="color: #7f8c8d; font-size: 14px;"><i>Version 1.0 - Premier Edition</i></p>
            <hr style="border: 1px solid #bdc3c7; margin: 20px 0;">
            <p style="font-size: 13px; line-height: 1.5;">
                <b>Your premier source for UPSC Current Affairs & Government News</b><br>
                Delivering curated headlines straight to your telegraph system daily.
            </p>
            <div style="text-align: left; margin: 20px 0;">
                <p style="font-size: 12px; color: #2c3e50;"><b>📰 FEATURES:</b></p>
                <ul style="font-size: 11px; color: #34495e; line-height: 1.4;">
                    <li>Multi-source news aggregation (The Hindu, PIB, Indian Express)</li>
                    <li>Smart keyword-based filtering system</li>
                    <li>Automated telegraph delivery system</li>
                    <li>Configurable scheduling & customization</li>
                    <li>Real-time news wire monitoring</li>
                </ul>
            </div>
            <p style="font-size: 10px; color: #95a5a6; font-family: 'Courier New', monospace;">
                For support and documentation, consult the README manual.
            </p>
        </div>
        """
        QMessageBox.about(self, "📰 About UPSC Daily Herald", about_text)
        
    def load_weekly_news(self, geography):
        """Load weekly news for selected geography"""
        try:
            self.log_message(f"📅 Loading weekly news for {geography.upper()}...")
            self.status_bar.showMessage(f"📡 Fetching weekly news for {geography}...")
            
            # Clear existing content
            for i in reversed(range(self.weekly_layout.count())):
                self.weekly_layout.itemAt(i).widget().setParent(None)
            
            weekly_data = get_weekly_news(self.config, geography)
            
            # Create summary header
            summary_frame = QFrame()
            summary_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                }
            """)
            
            summary_layout = QVBoxLayout()
            summary_info = QLabel(f"📊 {weekly_data['summary']['total_articles']} articles found for {weekly_data['summary']['date_range']}")
            summary_info.setStyleSheet("""
                color: #495057;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            """)
            summary_layout.addWidget(summary_info)
            summary_frame.setLayout(summary_layout)
            self.weekly_layout.addWidget(summary_frame)
            
            # Display news by category
            if geography == "all":
                for geo_name, articles in weekly_data.items():
                    if geo_name == "summary" or not articles:
                        continue
                        
                    # Category header
                    cat_label = QLabel(f"📍 {geo_name.upper()}")
                    cat_label.setStyleSheet("""
                        color: #c0392b;
                        font-family: 'Times New Roman', serif;
                        font-size: 16px;
                        font-weight: bold;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        padding: 15px 0 10px 0;
                        margin-top: 20px;
                    """)
                    self.weekly_layout.addWidget(cat_label)
                    
                    # Articles
                    for article in articles:
                        article_widget = self.create_weekly_article_widget(article)
                        self.weekly_layout.addWidget(article_widget)
            else:
                articles = weekly_data.get(geography, [])
                if articles:
                    for article in articles:
                        article_widget = self.create_weekly_article_widget(article)
                        self.weekly_layout.addWidget(article_widget)
                else:
                    no_news_label = QLabel("📰 No news available for this region")
                    no_news_label.setAlignment(Qt.AlignCenter)
                    no_news_label.setStyleSheet("""
                        color: #7f8c8d;
                        font-family: 'Times New Roman', serif;
                        font-size: 14px;
                        font-style: italic;
                        padding: 40px;
                    """)
                    self.weekly_layout.addWidget(no_news_label)
            
            # Add stretch to fill remaining space
            self.weekly_layout.addStretch()
            
            self.log_message(f"✅ Weekly news loaded successfully for {geography.upper()}")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
        except Exception as e:
            error_msg = f"❌ Failed to load weekly news: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "📅 Weekly News Error", f"Error loading weekly news: {str(e)}")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
    def create_weekly_article_widget(self, article):
        """Create widget for weekly article display"""
        article_frame = QFrame()
        article_frame.setStyleSheet("""
            QFrame {
                background-color: #fefefe;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                margin: 5px 0;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Source and date
        source_date_layout = QHBoxLayout()
        source_label = QLabel(f"📰 {article['source']}")
        source_label.setStyleSheet("""
            color: #c0392b;
            font-family: 'Times New Roman', serif;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        """)
        source_date_layout.addWidget(source_label)
        
        date_label = QLabel(f"📅 {article['date']}")
        date_label.setStyleSheet("""
            color: #6c757d;
            font-family: 'Courier New', monospace;
            font-size: 10px;
        """)
        source_date_layout.addWidget(date_label)
        source_date_layout.addStretch()
        
        layout.addLayout(source_date_layout)
        
        # Title
        title_label = QLabel(article['title'])
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 13px;
            font-weight: bold;
            line-height: 1.3;
            margin: 5px 0;
        """)
        layout.addWidget(title_label)
        
        # Link
        if article.get('link'):
            link_label = QLabel(f"🔗 <a href='{article['link']}' style='color: #3498db; text-decoration: none;'>Read Full Article</a>")
            link_label.setOpenExternalLinks(True)
            link_label.setStyleSheet("""
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #7f8c8d;
                margin-top: 5px;
            """)
            layout.addWidget(link_label)
        
        article_frame.setLayout(layout)
        return article_frame
        
    def load_monthly_news(self):
        """Load monthly top news"""
        try:
            self.log_message("📊 Loading monthly highlights...")
            self.status_bar.showMessage("📡 Fetching monthly highlights...")
            
            # Clear existing content
            for i in reversed(range(self.monthly_layout.count())):
                self.monthly_layout.itemAt(i).widget().setParent(None)
            
            monthly_data = get_monthly_news(self.config)
            
            # Create summary header
            summary_frame = QFrame()
            summary_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                }
            """)
            
            summary_layout = QVBoxLayout()
            summary_info = QLabel(f"📊 {len(monthly_data)} top stories from this month")
            summary_info.setStyleSheet("""
                color: #495057;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            """)
            summary_layout.addWidget(summary_info)
            summary_frame.setLayout(summary_layout)
            self.monthly_layout.addWidget(summary_frame)
            
            # Display monthly news
            for article in monthly_data:
                article_widget = self.create_monthly_article_widget(article)
                self.monthly_layout.addWidget(article_widget)
            
            # Add stretch to fill remaining space
            self.monthly_layout.addStretch()
            
            self.log_message("✅ Monthly highlights loaded successfully")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
        except Exception as e:
            error_msg = f"❌ Failed to load monthly news: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "📊 Monthly News Error", f"Error loading monthly news: {str(e)}")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
    def create_monthly_article_widget(self, article):
        """Create widget for monthly article display"""
        article_frame = QFrame()
        article_frame.setStyleSheet("""
            QFrame {
                background-color: #fefefe;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Header with source, date, and importance
        header_layout = QHBoxLayout()
        
        source_label = QLabel(f"📰 {article['source']}")
        source_label.setStyleSheet("""
            color: #c0392b;
            font-family: 'Times New Roman', serif;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        """)
        header_layout.addWidget(source_label)
        
        category_label = QLabel(f"📂 {article['category'].upper()}")
        category_label.setStyleSheet("""
            color: #8e44ad;
            font-family: 'Times New Roman', serif;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        """)
        header_layout.addWidget(category_label)
        
        importance_label = QLabel(f"⭐ {article['importance'].upper()}")
        importance_label.setStyleSheet("""
            color: #e74c3c;
            font-family: 'Times New Roman', serif;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        """)
        header_layout.addWidget(importance_label)
        
        date_label = QLabel(f"📅 {article['date']}")
        date_label.setStyleSheet("""
            color: #6c757d;
            font-family: 'Courier New', monospace;
            font-size: 10px;
        """)
        header_layout.addWidget(date_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel(article['title'])
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 15px;
            font-weight: bold;
            line-height: 1.3;
            margin: 10px 0;
        """)
        layout.addWidget(title_label)
        
        # Summary
        if article.get('summary'):
            summary_label = QLabel(article['summary'])
            summary_label.setWordWrap(True)
            summary_label.setStyleSheet("""
                color: #34495e;
                font-family: 'Times New Roman', serif;
                font-size: 12px;
                line-height: 1.4;
                margin: 10px 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            """)
            layout.addWidget(summary_label)
        
        # Link
        if article.get('link'):
            link_label = QLabel(f"🔗 <a href='{article['link']}' style='color: #3498db; text-decoration: none;'>Read Full Article</a>")
            link_label.setOpenExternalLinks(True)
            link_label.setStyleSheet("""
                font-family: 'Courier New', monospace;
                font-size: 11px;
                color: #7f8c8d;
                margin-top: 10px;
            """)
            layout.addWidget(link_label)
        
        article_frame.setLayout(layout)
        return article_frame
        
    def load_upsc_questions(self):
        """Load UPSC practice questions"""
        try:
            self.log_message("🎓 Generating UPSC practice questions...")
            self.status_bar.showMessage("📡 Generating practice questions...")
            
            # Clear existing content
            for i in reversed(range(self.upsc_layout.count())):
                self.upsc_layout.itemAt(i).widget().setParent(None)
            
            questions_data = generate_upsc_questions(self.config)
            
            # Create summary header
            summary_frame = QFrame()
            summary_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                }
            """)
            
            summary_layout = QVBoxLayout()
            summary_info = QLabel(f"🎓 {len(questions_data)} practice questions generated from recent news")
            summary_info.setStyleSheet("""
                color: #495057;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            """)
            summary_layout.addWidget(summary_info)
            summary_frame.setLayout(summary_layout)
            self.upsc_layout.addWidget(summary_frame)
            
            # Display questions
            for idx, question in enumerate(questions_data, 1):
                question_widget = self.create_upsc_question_widget(question, idx)
                self.upsc_layout.addWidget(question_widget)
            
            # Add stretch to fill remaining space
            self.upsc_layout.addStretch()
            
            self.log_message("✅ UPSC practice questions generated successfully")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
        except Exception as e:
            error_msg = f"❌ Failed to generate UPSC questions: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "🎓 UPSC Questions Error", f"Error generating questions: {str(e)}")
            self.status_bar.showMessage("📰 Ready to deliver the news...")
            
    def create_upsc_question_widget(self, question, index):
        """Create widget for UPSC question display"""
        question_frame = QFrame()
        question_frame.setStyleSheet("""
            QFrame {
                background-color: #fefefe;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Question header
        header_layout = QHBoxLayout()
        
        question_num = QLabel(f"Q{index}.")
        question_num.setStyleSheet("""
            color: #8e44ad;
            font-family: 'Times New Roman', serif;
            font-size: 16px;
            font-weight: bold;
            min-width: 40px;
        """)
        header_layout.addWidget(question_num)
        
        topic_label = QLabel(f"📚 {question['topic']}")
        topic_label.setStyleSheet("""
            color: #2980b9;
            font-family: 'Times New Roman', serif;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        """)
        header_layout.addWidget(topic_label)
        
        difficulty_label = QLabel(f"🎯 {question['difficulty'].upper()}")
        difficulty_color = "#e74c3c" if question['difficulty'] == "high" else "#f39c12" if question['difficulty'] == "medium" else "#27ae60"
        difficulty_label.setStyleSheet(f"""
            color: {difficulty_color};
            font-family: 'Times New Roman', serif;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        """)
        header_layout.addWidget(difficulty_label)
        
        date_label = QLabel(f"📅 {question['date']}")
        date_label.setStyleSheet("""
            color: #6c757d;
            font-family: 'Courier New', monospace;
            font-size: 10px;
        """)
        header_layout.addWidget(date_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Question text
        question_text = QLabel(question['question'])
        question_text.setWordWrap(True)
        question_text.setStyleSheet("""
            color: #2c3e50;
            font-family: 'Times New Roman', serif;
            font-size: 14px;
            font-weight: bold;
            line-height: 1.4;
            margin: 15px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #8e44ad;
        """)
        layout.addWidget(question_text)
        
        # Context
        context_label = QLabel(f"📰 Context: {question['context']}")
        context_label.setWordWrap(True)
        context_label.setStyleSheet("""
            color: #34495e;
            font-family: 'Times New Roman', serif;
            font-size: 12px;
            line-height: 1.3;
            margin: 10px 0;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(context_label)
        
        # Answer hints
        hints_label = QLabel("💡 Key Points to Consider:")
        hints_label.setStyleSheet("""
            color: #c0392b;
            font-family: 'Times New Roman', serif;
            font-size: 12px;
            font-weight: bold;
            margin: 10px 0 5px 0;
        """)
        layout.addWidget(hints_label)
        
        hints_text = "• " + "\n• ".join(question['answer_hints'])
        hints_display = QLabel(hints_text)
        hints_display.setWordWrap(True)
        hints_display.setStyleSheet("""
            color: #7f8c8d;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            line-height: 1.4;
            margin: 5px 0;
            padding: 10px;
            background-color: #fff3cd;
            border-radius: 5px;
        """)
        layout.addWidget(hints_display)
        
        # Source news
        source_label = QLabel(f"📰 Based on: {question['source_news']}")
        source_label.setStyleSheet("""
            color: #6c757d;
            font-family: 'Courier New', monospace;
            font-size: 10px;
            font-style: italic;
            margin-top: 10px;
        """)
        layout.addWidget(source_label)
        
        question_frame.setLayout(layout)
        return question_frame
            
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(self, '📰 Close Daily Herald',
                                   "Are you sure you want to close the Daily Herald?\n\nThis will stop the news scheduler and telegraph system.",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.shutdown()
            event.accept()
        else:
            event.ignore()
            
    def shutdown(self):
        """Proper application shutdown"""
        try:
            self.log_message("📰 Shutting down Daily Herald - Telegraph system going offline...")
            if self.scheduler:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")
            
            # Stop the status timer
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            QApplication.quit()
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            QApplication.quit()