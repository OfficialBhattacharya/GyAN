from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QTimeEdit, QListWidget, QListWidgetItem, QPushButton, 
    QGroupBox, QCheckBox, QMessageBox, QTextEdit, QSpinBox
)
from PyQt5.QtCore import QTime
from PyQt5.QtGui import QFont
import copy

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = copy.deepcopy(config)
        self.init_ui()
        self.load_config_values()
        
    def init_ui(self):
        self.setWindowTitle("UPSC News Aggregator Settings")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        
        # Email Settings Group
        email_group = QGroupBox("Email Configuration")
        email_layout = QFormLayout()
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("your.email@example.com")
        email_layout.addRow("Recipient Email:", self.email_edit)
        
        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText("smtp.gmail.com")
        email_layout.addRow("SMTP Server:", self.smtp_server_edit)
        
        self.smtp_port_edit = QSpinBox()
        self.smtp_port_edit.setRange(1, 65535)
        self.smtp_port_edit.setValue(587)
        email_layout.addRow("SMTP Port:", self.smtp_port_edit)
        
        self.smtp_username_edit = QLineEdit()
        self.smtp_username_edit.setPlaceholderText("your.email@example.com")
        email_layout.addRow("SMTP Username:", self.smtp_username_edit)
        
        self.smtp_password_edit = QLineEdit()
        self.smtp_password_edit.setEchoMode(QLineEdit.Password)
        self.smtp_password_edit.setPlaceholderText("App Password or Account Password")
        email_layout.addRow("SMTP Password:", self.smtp_password_edit)
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        # Schedule Settings Group
        schedule_group = QGroupBox("Schedule Configuration")
        schedule_layout = QFormLayout()
        
        self.send_time_edit = QTimeEdit()
        self.send_time_edit.setDisplayFormat("HH:mm")
        schedule_layout.addRow("Daily Send Time:", self.send_time_edit)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        
        # News Sources Group
        sources_group = QGroupBox("News Sources")
        sources_layout = QVBoxLayout()
        
        self.source_checkboxes = {}
        sources = [
            ("thehindu", "The Hindu (National Section)"),
            ("pib", "Press Information Bureau (PIB)"),
            ("indianexpress", "Indian Express (India Section)")
        ]
        
        for source_id, source_name in sources:
            checkbox = QCheckBox(source_name)
            self.source_checkboxes[source_id] = checkbox
            sources_layout.addWidget(checkbox)
        
        sources_group.setLayout(sources_layout)
        layout.addWidget(sources_group)
        
        # Keywords Group
        keywords_group = QGroupBox("UPSC Relevant Keywords")
        keywords_layout = QVBoxLayout()
        
        self.keywords_edit = QTextEdit()
        self.keywords_edit.setMaximumHeight(100)
        self.keywords_edit.setPlaceholderText("Enter keywords separated by commas (e.g., UPSC, government, policy, economy)")
        keywords_layout.addWidget(self.keywords_edit)
        
        keywords_group.setLayout(keywords_layout)
        layout.addWidget(keywords_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Email")
        test_btn.clicked.connect(self.test_email)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_config_values(self):
        """Load current configuration values into the UI"""
        self.email_edit.setText(self.config.get('email', ''))
        self.smtp_server_edit.setText(self.config.get('smtp_server', 'smtp.gmail.com'))
        self.smtp_port_edit.setValue(self.config.get('smtp_port', 587))
        self.smtp_username_edit.setText(self.config.get('smtp_username', ''))
        self.smtp_password_edit.setText(self.config.get('smtp_password', ''))
        
        # Set time
        time_str = self.config.get('send_time', '07:00')
        hour, minute = map(int, time_str.split(':'))
        self.send_time_edit.setTime(QTime(hour, minute))
        
        # Set source checkboxes
        enabled_sources = self.config.get('sources', [])
        for source_id, checkbox in self.source_checkboxes.items():
            checkbox.setChecked(source_id in enabled_sources)
        
        # Set keywords
        keywords = self.config.get('keywords', [])
        self.keywords_edit.setPlainText(', '.join(keywords))
        
    def save_settings(self):
        """Validate and save settings"""
        # Validate email settings
        email = self.email_edit.text().strip()
        smtp_username = self.smtp_username_edit.text().strip()
        smtp_password = self.smtp_password_edit.text().strip()
        
        if email and (not smtp_username or not smtp_password):
            QMessageBox.warning(self, "Validation Error", 
                              "Please provide both SMTP username and password for email functionality.")
            return
        
        # Get selected sources
        selected_sources = []
        for source_id, checkbox in self.source_checkboxes.items():
            if checkbox.isChecked():
                selected_sources.append(source_id)
        
        if not selected_sources:
            QMessageBox.warning(self, "Validation Error", 
                              "Please select at least one news source.")
            return
        
        # Parse keywords
        keywords_text = self.keywords_edit.toPlainText().strip()
        keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
        
        if not keywords:
            QMessageBox.warning(self, "Validation Error", 
                              "Please provide at least one keyword for filtering news.")
            return
        
        # Update configuration
        self.config.update({
            'email': email,
            'smtp_server': self.smtp_server_edit.text().strip(),
            'smtp_port': self.smtp_port_edit.value(),
            'smtp_username': smtp_username,
            'smtp_password': smtp_password,
            'send_time': self.send_time_edit.time().toString("HH:mm"),
            'sources': selected_sources,
            'keywords': keywords
        })
        
        self.accept()
        
    def test_email(self):
        """Test email configuration by sending a test email"""
        from email_manager import send_news_email
        
        # Create temporary config with current settings
        test_config = {
            'email': self.email_edit.text().strip(),
            'smtp_server': self.smtp_server_edit.text().strip(),
            'smtp_port': self.smtp_port_edit.value(),
            'smtp_username': self.smtp_username_edit.text().strip(),
            'smtp_password': self.smtp_password_edit.text().strip()
        }
        
        if not all([test_config['email'], test_config['smtp_username'], test_config['smtp_password']]):
            QMessageBox.warning(self, "Test Failed", 
                              "Please fill in all email configuration fields before testing.")
            return
        
        # Send test email
        test_news = [{
            'source': 'TEST',
            'title': 'This is a test email from UPSC News Aggregator',
            'link': 'https://example.com'
        }]
        
        try:
            send_news_email(test_config, test_news)
            QMessageBox.information(self, "Test Successful", 
                                  "Test email sent successfully! Check your inbox.")
        except Exception as e:
            QMessageBox.critical(self, "Test Failed", 
                               f"Failed to send test email:\n{str(e)}")
    
    def get_updated_config(self):
        """Return the updated configuration"""
        return self.config 