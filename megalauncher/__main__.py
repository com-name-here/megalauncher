import sys
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget,
    QHBoxLayout, QStatusBar, QLabel, QMenuBar, QMessageBox, QCheckBox,
    QSizePolicy, QProgressDialog
)

from launcher import main as launch_main, stop_mac, is_mac_running, check_mac_status, mac_launcher
from updater import check_for_updates, reinstall_mac
from util import get_installed_version, load_config, save_config
import icon_rc


class LaunchThread(QThread):
    update_log = Signal(str)
    launch_completed = Signal()

    def __init__(self, launch_with_tf2):
        super().__init__()
        self.launch_with_tf2 = launch_with_tf2

    def run(self):
        launch_main(self.launch_with_tf2, self.update_log.emit)
        self.launch_completed.emit()


class UpdateThread(QThread):
    finished = Signal(str)

    def run(self):
        self.finished.emit(check_for_updates())


class ReinstallThread(QThread):
    finished = Signal(str)

    def run(self):
        self.finished.emit(reinstall_mac())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MegaLauncher")
        self.setGeometry(100, 100, 410, 400)

        self.launch_button = QPushButton("Start")
        self.tf2_checkbox = QCheckBox("Launch with TF2")
        self.log_display = QTextEdit()

        self.status_bar = QStatusBar(self)
        self.version_label = QLabel()
        self.link_label = QLabel()

        self.progress_dialog = None

        self.launch_thread = None
        self.update_thread = None
        self.reinstall_thread = None

        self.setup_ui()
        self.create_menu_bar()
        self.create_status_bar()

        self.log_lines = []
        self.max_log_lines = 100

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_status)
        self.status_timer.start(1000)

        mac_launcher.add_observer(self.update_ui)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        button_layout = QHBoxLayout()

        self.launch_button.clicked.connect(self.toggle_launch)
        self.launch_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.launch_button)

        self.tf2_checkbox.setChecked(self.load_tf2_checkbox_state())
        self.tf2_checkbox.stateChanged.connect(self.save_tf2_checkbox_state)
        button_layout.addWidget(self.tf2_checkbox)

        layout.addLayout(button_layout)

        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        if sys.platform == "win32":
            app.setWindowIcon(QIcon(":/icon.ico"))
        else:
            app.setWindowIcon(QIcon(":/icon.png"))

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Check For Updates", self.check_for_updates)
        file_menu.addAction("Exit", self.close)

        options_menu = menu_bar.addMenu("Options")
        options_menu.addAction("Reinstall", self.reinstall)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About", self.show_about)
        help_menu.addAction("About Qt", QApplication.aboutQt)

    def create_status_bar(self):
        self.setStatusBar(self.status_bar)

        self.status_bar.addWidget(self.version_label)
        self.status_bar.addPermanentWidget(QWidget(), 1)

        self.status_bar.addPermanentWidget(self.link_label, 1)

        self.update_ui()

    def toggle_launch(self):
        if is_mac_running():
            self.stop_application()
        else:
            self.launch_application()
        self.update_ui()

    def launch_application(self):
        self.launch_button.setText("Stop")
        self.tf2_checkbox.setEnabled(False)
        self.update_log("--- New Launch ---")

        self.launch_thread = LaunchThread(self.tf2_checkbox.isChecked())
        self.launch_thread.update_log.connect(self.update_log)
        self.launch_thread.launch_completed.connect(self.update_ui)
        self.launch_thread.start()

    @staticmethod
    def load_tf2_checkbox_state():
        config = load_config()
        return config.getboolean("launcher", "tf2_checkbox", fallback=False)

    @staticmethod
    def save_tf2_checkbox_state(state):
        config = load_config()
        config.set("launcher", "tf2_checkbox", str(bool(state)))
        save_config(config)

    def check_for_updates(self):
        self.update_log("Checking for updates...")
        self.launch_button.setEnabled(False)

        self.update_thread = UpdateThread()
        self.update_thread.finished.connect(self.on_update_finished)
        self.update_thread.start()

    def reinstall(self):
        reply = QMessageBox.question(
            self, "Confirm Reinstall",
            "Are you sure you want to reinstall MAC?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.start_reinstall()

    def start_reinstall(self):
        self.update_log("Reinstalling...")
        self.launch_button.setEnabled(False)

        self.progress_dialog = QProgressDialog("Reinstalling...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("Reinstalling")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        # noinspection PyTypeChecker
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        self.reinstall_thread = ReinstallThread()
        self.reinstall_thread.finished.connect(self.on_reinstall_finished)
        self.reinstall_thread.start()

    def on_reinstall_finished(self, result):
        self.progress_dialog.close()
        self.update_log(result)
        self.update_ui()
        self.launch_button.setEnabled(True)
        QMessageBox.information(self, "Reinstall Complete", result)

    def on_update_finished(self, result):
        self.update_log(result)
        self.update_ui()
        self.launch_button.setEnabled(True)
        QMessageBox.information(self, "Updater", result)

    def show_about(self):
        QMessageBox.about(
            self, "About MegaLauncher",
            "MegaLauncher\n\n"
            "A basic GUI for launching and updating MegaAntiCheat.\n\n"
            "https://github.com/com-name-here/megalauncher\n"
        )

    def update_log(self, text):
        self.log_lines.append(text)
        if len(self.log_lines) > self.max_log_lines:
            self.log_lines = self.log_lines[-self.max_log_lines:]

        self.log_display.clear()
        for line in self.log_lines:
            color = QColor("gray")
            if line.startswith("INFO"):
                color = QColor("white")
            elif line.startswith("WARN"):
                color = QColor("yellow")
            elif line.startswith("ERROR"):
                color = QColor("red")

            self.log_display.setTextColor(color)
            self.log_display.append(line)

        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_version_display(self):
        version = get_installed_version()
        self.version_label.setText(f"MegaAntiCheat {version}" if version else "")

    def update_ui(self):
        self.update_version_display()
        if is_mac_running():
            self.launch_button.setText("Stop")
            self.tf2_checkbox.setEnabled(False)
            status_text = "Web Interface at: <a href='http://127.0.0.1:3621'>http://127.0.0.1:3621</a>"
            self.link_label.setText(status_text)
            self.link_label.setOpenExternalLinks(True)
        else:
            self.launch_button.setText("Start")
            self.tf2_checkbox.setEnabled(True)
            self.link_label.clear()

    @staticmethod
    def check_status():
        check_mac_status()

    def stop_application(self):
        stop_mac()
        self.update_ui()
        self.update_log("MAC has been stopped.")

    def closeEvent(self, event):
        if is_mac_running():
            self.stop_application()
        mac_launcher.remove_observer(self.update_ui)
        self.save_tf2_checkbox_state(self.tf2_checkbox.isChecked())
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
