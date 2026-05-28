import sys
from PyQt5.QtWidgets import QApplication
from ui_window import UpVBDesktop

if __name__ == '__main__':
    # Create the application instance
    app = QApplication(sys.argv)
    
    # Ensure the app doesn't close if only the tray icon is visible
    app.setQuitOnLastWindowClosed(False)
    
    # Initialize and show the main window
    window = UpVBDesktop()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())
