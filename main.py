import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow

def main():
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("UPSC News Aggregator")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("UPSC Tools")
    
    # Allow app to close when main window is closed
    app.setQuitOnLastWindowClosed(True)
    
    try:
        # Create and show the main window
        window = MainWindow()
        window.show()
        
        # Keep a reference to prevent garbage collection
        app.main_window = window
        
        # Start the application event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "Application Error", 
                           f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()