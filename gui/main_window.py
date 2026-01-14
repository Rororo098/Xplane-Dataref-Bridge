from __future__ import annotations
import logging
import asyncio
from PyQt6.QtWidgets import QApplication
from core.input_mapper import InputMapper
from core.profile_manager import ProfileManager
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QStatusBar,
    QPushButton,
    QMessageBox,
    QMenu,
    QMenuBar,
    QInputDialog,
    QFileDialog,
    QApplication,
)
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl


from core.hid.hid_manager import HIDManager
from core.arduino.arduino_manager import ArduinoManager
from core.variable_store import VariableStore

from .hid_panel import HIDPanel
from .arduino_panel import ArduinoPanel
from .output_panel import OutputPanel
from .settings_panel import SettingsPanel
from .input_panel import InputPanel
from core.logic_engine import LogicEngine
from core.variable_store import VariableType

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    # Constants for UI texts
    LOAD_PROFILE_ACTION = "Load Profile"
    SAVE_PROFILE_ACTION = "Save Profile"
    IMPORT_PROFILE_ACTION = "Import Profile..."
    EXPORT_PROFILE_ACTION = "Export Profile..."

    # Signals for thread-safe communication
    arduino_input_signal = pyqtSignal(str, str, float)  # port, key, value

    def __init__(
        self,
        xplane_conn,
        dataref_manager,
        arduino_manager: ArduinoManager,
        hid_manager: HIDManager,
        variable_store=None,
    ) -> None:
        super().__init__()

        self.xplane_conn = xplane_conn
        self.dataref_manager = dataref_manager
        self.arduino_manager = arduino_manager
        self.hid_manager = hid_manager

        # Use the variable store passed from main
        if variable_store is not None:
            self.variable_store = variable_store
        else:
            self.variable_store = VariableStore()

        # Create input mapper with all dependencies
        self.input_mapper = InputMapper(
            xplane_conn,
            dataref_manager,
            hid_manager=hid_manager,
            arduino_manager=arduino_manager,
            variable_store=self.variable_store,
        )

        # Connect variable store to input mapper for updates
        self.variable_store.register_listener(self._on_variable_update)

        # Create logic engine and link back to input mapper
        self.logic_engine = LogicEngine(
            xplane_conn, self.input_mapper, arduino_manager=arduino_manager
        )
        self.logic_engine.variable_store = self.variable_store

        # Give InputMapper the reference to LogicEngine
        self.input_mapper.logic_engine = self.logic_engine

        # Link Logic Engine to Dataref Manager for search discovery
        self.dataref_manager.logic_engine = self.logic_engine

        # Create profile manager
        self.profile_manager = ProfileManager(
            arduino_manager,
            self.input_mapper,
            xplane_conn,
            self.logic_engine,
            self.hid_manager,
        )

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._setup_callbacks()
        self._start_managers()

        # Aircraft tracking for auto-profile switching
        self._current_icao = ""
        self._icao_buffer = [0] * 40
        self._auto_profile_enabled = True  # Could be a setting

        # Connect the signal to the async handler
        self.arduino_input_signal.connect(self._handle_arduino_input)

        # Set window icon if not already set by application
        from PyQt6.QtGui import QIcon
        import os

        # Try ICO format first (for Windows), fallback to PNG
        icon_path_ico = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resources", "icon.ico"
        )
        icon_path_png = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources",
            "Gemini_Generated_Image_5v3gkv5v3gkv5v3g-removebg-preview.png",
        )
        icon_path_fallback = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources",
            "Gemini_Generated_Image_5v3gkv5v3gkv5v3g-removebg-preview.png",
        )

        # Set application icon (for taskbar and window)
        if os.path.exists(icon_path_ico):
            app_icon = QIcon(icon_path_ico)
            self.setWindowIcon(app_icon)
        elif os.path.exists(icon_path_png):
            app_icon = QIcon(icon_path_png)
            self.setWindowIcon(app_icon)
        else:
            app_icon = QIcon(icon_path_fallback)
            self.setWindowIcon(app_icon)

        # Set application icon for the entire app (fixes taskbar issue)
        if QApplication.instance():
            QApplication.instance().setWindowIcon(app_icon)

        # Status update timer
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)

        # Timer for logic engine processing
        self._logic_timer = QTimer()
        self._logic_timer.timeout.connect(self.logic_engine.process_tick)
        self._logic_timer.start(100)  # Process every 100ms

        # Load default profile on startup
        QTimer.singleShot(500, self._load_default_profile)

        # Initialize donation popup timer
        self._donation_timer = QTimer()
        self._donation_timer.setSingleShot(True)  # Only show once per startup
        self._donation_timer.timeout.connect(self._show_donation_popup)
        self._donation_timer.setInterval(1500)  # Show after 1.5 seconds

        # Start the donation popup timer after the window is fully initialized
        self._donation_timer.start()

    def _load_default_profile(self):
        """Load default profile after startup."""
        if self.profile_manager.load_profile("default"):
            log.info("Loaded default profile")
            if hasattr(self, "output_panel"):
                self.output_panel.refresh_from_manager()
                if hasattr(self, "output_panel") and hasattr(
                    self.output_panel, "restore_state"
                ):
                    self.output_panel.restore_state()
            # Refresh all search helpers now that IDs are loaded
            self.refresh_search_helpers()
        else:
            log.info("No default profile found (fresh start)")

    def _setup_ui(self) -> None:
        self.setWindowTitle("X-Plane Dataref Bridge")
        self.setMinimumSize(900, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Connection status bar at top
        status_layout = QHBoxLayout()

        self.xplane_status = QLabel("X-Plane: Disconnected")
        self.xplane_status.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.xplane_status)

        status_layout.addStretch()

        # PayPal donation button
        self.paypal_btn = QPushButton("❤️ Donate (PayPal)")
        self.paypal_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.paypal_btn.clicked.connect(self._open_paypal_page)
        status_layout.addWidget(self.paypal_btn)

        # Stripe donation button
        self.stripe_btn = QPushButton("💳 Donate (Stripe)")
        self.stripe_btn.setStyleSheet("""
            QPushButton {
                background-color: #635bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5951e6;
            }
        """)
        self.stripe_btn.clicked.connect(self._open_stripe_page)
        status_layout.addWidget(self.stripe_btn)

        self.connect_btn = QPushButton("Connect to X-Plane")
        self.connect_btn.clicked.connect(self._toggle_xplane_connection)
        status_layout.addWidget(self.connect_btn)

        self.sync_btn = QPushButton("Auto-Sync Output")
        self.sync_btn.setToolTip(
            "Tell X-Plane to send data output to this app (ISE4 + DSEL)."
        )
        self.sync_btn.setEnabled(False)
        self.sync_btn.clicked.connect(self._toggle_output_sync)
        status_layout.addWidget(self.sync_btn)

        layout.addLayout(status_layout)

        # Tab widget
        self.tabs = QTabWidget()

        # Output Config panel (Data Center)
        self.output_panel = OutputPanel(
            self.dataref_manager,
            self.xplane_conn,
            self.arduino_manager,
            self.variable_store,
            self.logic_engine,
        )
        self.tabs.addTab(self.output_panel, "Output Config")

        # Input Config panel (Controller Lab)
        self.input_panel = InputPanel(
            self.hid_manager,
            self.input_mapper,
            self.profile_manager,
            self.variable_store,
        )
        self.tabs.addTab(self.input_panel, "Input Config")

        # Hardware panel (Device Manager)
        self.arduino_panel = ArduinoPanel(self.arduino_manager, self.dataref_manager)
        self.tabs.addTab(self.arduino_panel, "Hardware")

        # Settings panel
        self.settings_panel = SettingsPanel()
        self.tabs.addTab(self.settings_panel, "Settings")

        layout.addWidget(self.tabs)

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")

        save_action = QAction(self.SAVE_PROFILE_ACTION, self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_profile_dialog)
        file_menu.addAction(save_action)

        load_action = QAction(self.LOAD_PROFILE_ACTION, self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_profile_dialog)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        # Import / Export
        import_action = QAction("Import Profile...", self)
        import_action.triggered.connect(self._import_profile_dialog)
        file_menu.addAction(import_action)

        export_action = QAction("Export Profile...", self)
        export_action.triggered.connect(self._export_profile_dialog)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help Menu
        help_menu = menu_bar.addMenu("Help")

        open_log_action = QAction("Open Log File", self)
        open_log_action.triggered.connect(self._open_log_file)
        help_menu.addAction(open_log_action)

        # Donation Action
        donation_popup_action = QAction("Show Donation Appeal", self)
        donation_popup_action.triggered.connect(self._show_donation_popup)
        help_menu.addAction(donation_popup_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _save_profile_dialog(self):
        name, ok = QInputDialog.getText(
            self, self.SAVE_PROFILE_ACTION, "Profile Name:", text="default"
        )
        if ok and name:
            if self.profile_manager.save_profile(name):
                self.status_bar.showMessage(
                    f"Profile '{name}' saved successfully", 3000
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to save profile")

    def _load_profile_dialog(self):
        name, ok = QInputDialog.getText(
            self, self.LOAD_PROFILE_ACTION, "Profile Name:", text="default"
        )
        if ok and name:
            if self.profile_manager.load_profile(name):
                self.status_bar.showMessage(
                    f"Profile '{name}' loaded successfully", 3000
                )
                # Refresh UI
                if hasattr(self, "output_panel") and hasattr(
                    self.output_panel, "restore_state"
                ):
                    self.output_panel.refresh_from_manager()
                    self.output_panel.restore_state()
            else:
                QMessageBox.warning(
                    self, "Error", f"Profile '{name}' not found or failed to load"
                )

    def _import_profile_dialog(self):
        """Dialog to import a profile from external file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Profile JSON", "", "JSON Files (*.json)"
        )
        if not file_path:
            return

        from pathlib import Path

        path = Path(file_path)

        imported_name = self.profile_manager.import_profile(path)
        if imported_name:
            QMessageBox.information(
                self, "Success", f"Profile imported successfully as '{imported_name}'"
            )
            # Ask to load?
            if (
                QMessageBox.question(
                    self,
                    self.LOAD_PROFILE_ACTION,
                    f"Do you want to load the imported profile '{imported_name}' now?",
                )
                == QMessageBox.StandardButton.Yes
            ):
                self.profile_manager.load_profile(imported_name)
                # Refresh UI
                if hasattr(self, "output_panel") and hasattr(
                    self.output_panel, "restore_state"
                ):
                    self.output_panel.refresh_from_manager()
                    self.output_panel.restore_state()
        else:
            QMessageBox.critical(
                self, "Error", "Failed to import profile. Check log for details."
            )

    def _export_profile_dialog(self):
        """Dialog to export current profile to external file."""
        # Get current profile name? Or just ask user which one to export?
        # For simplicity, let's export the currently active state as a new file

        name, ok = QInputDialog.getText(
            self,
            "Export Profile",
            "Enter name for exported file (without .json):",
            text="my_profile_backup",
        )
        if not ok or not name:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile Location", f"{name}.json", "JSON Files (*.json)"
        )
        if not file_path:
            return

        from pathlib import Path

        if self.profile_manager.export_profile(name, Path(file_path)):
            QMessageBox.information(self, "Success", f"Profile exported to {file_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to export profile.")

    def _open_log_file(self):
        """Open the application log file."""
        log_file = "bridge_log.txt"
        from pathlib import Path
        import os

        path = Path.cwd() / log_file
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            QMessageBox.information(
                self,
                "Log File",
                "Log file not found yet (maybe write something first?)",
            )

    def _open_paypal_page(self):
        """Open the PayPal donation page in the default browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        QDesktopServices.openUrl(QUrl("https://www.paypal.me/Ruzu26"))

    def _open_stripe_page(self):
        """Open the Stripe donation page in the default browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        QDesktopServices.openUrl(
            QUrl("https://donate.stripe.com/test_dRm14n4gE5Av51d0cV7Vm00")
        )

    def _show_donation_popup(self):
        """Show a dedicated donation popup window."""
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QLabel,
            QPushButton,
            QHBoxLayout,
        )
        from PyQt6.QtCore import QTimer, Qt

        # Create a custom dialog instead of QMessageBox to have more control
        dialog = QDialog(self)
        dialog.setWindowTitle("Support X-Plane Dataref Bridge Development")
        dialog.setModal(True)
        dialog.resize(550, 350)
        # Remove the close button (X) from the window
        dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
        )

        layout = QVBoxLayout()

        # Add content
        title_label = QLabel("<h3>Enjoying X-Plane Dataref Bridge?</h3>")
        title_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(title_label)

        content_label = QLabel(
            "<p>If this tool enhances your flight simulation experience, "
            "please consider supporting its continued development!</p>"
            "<p>Your donation helps maintain and improve this project, "
            "ensuring it remains free and functional for the community.</p>"
            "<p><b>Choose your preferred donation method:</b></p>"
        )
        content_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(content_label)

        # PayPal link
        paypal_label = QLabel(
            "<p>PayPal: <a href='https://www.paypal.me/Ruzu26'>https://www.paypal.me/Ruzu26</a></p>"
        )
        paypal_label.setTextFormat(Qt.TextFormat.RichText)
        paypal_label.setOpenExternalLinks(True)  # Allow clicking links
        layout.addWidget(paypal_label)

        # Stripe link
        stripe_label = QLabel(
            "<p>Stripe: <a href='https://donate.stripe.com/test_dRm14n4gE5Av51d0cV7Vm00'>https://donate.stripe.com/test_dRm14n4gE5Av51d0cV7Vm00</a></p>"
        )
        stripe_label.setTextFormat(Qt.TextFormat.RichText)
        stripe_label.setOpenExternalLinks(True)  # Allow clicking links
        layout.addWidget(stripe_label)

        # Countdown label
        countdown_label = QLabel("You can dismiss this message in 8 seconds...")
        layout.addWidget(countdown_label)

        # Buttons layout
        button_layout = QHBoxLayout()

        # PayPal Donate button (always enabled)
        paypal_button = QPushButton("Donate via PayPal")
        paypal_button.clicked.connect(lambda: self._open_paypal_page())
        button_layout.addWidget(paypal_button)

        # Stripe Donate button (always enabled)
        stripe_button = QPushButton("Donate via Stripe")
        stripe_button.clicked.connect(lambda: self._open_stripe_page())
        button_layout.addWidget(stripe_button)

        # Maybe Later button (initially disabled)
        maybe_later_button = QPushButton("Maybe Later")
        maybe_later_button.setEnabled(False)
        maybe_later_button.clicked.connect(dialog.reject)
        button_layout.addWidget(maybe_later_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        # Countdown mechanism
        countdown = 8
        countdown_label.setText(
            f"You can dismiss this message in {countdown} seconds..."
        )

        def update_countdown():
            nonlocal countdown
            countdown -= 1
            if countdown > 0:
                # Check if the dialog still exists before updating
                if dialog.isVisible():
                    countdown_label.setText(
                        f"You can dismiss this message in {countdown} seconds..."
                    )
            else:
                # Check if the dialog still exists before updating
                if dialog.isVisible():
                    countdown_label.setText("You may now close this message")
                    maybe_later_button.setEnabled(True)
                timer.stop()

        timer = QTimer(self)
        timer.timeout.connect(update_countdown)
        timer.start(1000)  # Update every second

        # Show the dialog
        dialog.exec()

        # Stop the timer when dialog closes to prevent errors
        timer.stop()

    def _show_about_dialog(self):
        """Show About dialog."""
        # Create a custom message box to properly handle HTML links
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("About X-Plane Dataref Bridge")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(
            "<h3>X-Plane Dataref Bridge</h3>"
            "<p>Version: 1.0.0 (Beta)</p>"
            "<p>A tool to bridge X-Plane datarefs to Arduino and HID devices.</p>"
            "<p><b>Beta Testing:</b></p>"
            "<p>If you encounter issues, please use 'Help -> Open Log File' "
            "and send the 'bridge_log.txt' to the developer.</p>"
            "<p><b>Support Development:</b></p>"
            "<p>If you find this tool valuable, consider supporting its continued development "
            "by making a donation via <a href='https://www.paypal.me/Ruzu26'>PayPal</a> or "
            "<a href='https://donate.stripe.com/test_dRm14n4gE5Av51d0cV7Vm00'>Stripe</a>. "
            "Your contribution helps maintain and improve this project!</p>"
        )
        msg_box.exec()

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _on_arduino_input_received(self, port: str, key: str, value: float) -> None:
        """
        Called from Arduino manager thread when input is received.
        Emits a signal to handle it in the main thread.
        """
        self.arduino_input_signal.emit(port, key, value)

    def _handle_arduino_input(self, port: str, key: str, value: float) -> None:
        """
        Handle Arduino input in the main thread (slot for the signal).
        """
        log.debug("Arduino input: %s/%s = %.2f", port, key, value)

        # 1. Check if this key matches a sequence event
        if value != 0:  # Only trigger sequences on press (not release)
            # Try to execute sequence by key first
            if hasattr(self.output_panel, "execute_sequence_by_key"):
                if self.output_panel.execute_sequence_by_key(key):
                    log.info("Executed sequence for key: %s", key)
                    return  # If sequence was executed, don't process as regular input

        # 2. Pass to Input Panel for "Learn" mode
        if value != 0:  # Press or Rotate
            self.input_panel.handle_input_signal(key, port)

        # 3. Process actual logic
        task = asyncio.create_task(self._process_arduino_input(port, key, value))
        # Store task to prevent garbage collection
        if not hasattr(self, "_active_tasks"):
            self._active_tasks = set()
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))

    async def _process_arduino_input(self, port: str, key: str, value: float) -> None:
        """Process Arduino input asynchronously."""
        try:
            await self.input_mapper.process_input(port, key, value)
        except Exception as e:
            log.error("Error processing input %s: %s", key, e)

    def _setup_callbacks(self) -> None:
        """Setup callbacks for managers."""
        # X-Plane connection status
        self.xplane_conn.on_connection_changed = self._on_xplane_connection_changed

        # X-Plane dataref updates -> bridge -> Arduino devices
        self.xplane_conn.on_dataref_update = self._on_dataref_update

        # Arduino input -> emit signal (thread-safe)
        self.arduino_manager.on_input_received = self._on_arduino_input_received

        # Arduino DREF/CMD commands -> X-Plane
        self.arduino_manager.on_dataref_write = self._on_arduino_dataref_write
        self.arduino_manager.on_command_send = self._on_arduino_command_send

        # Connect to variable store updates
        if hasattr(self, "variable_store"):
            self.variable_store.register_listener(self._on_variable_update)

    def _on_arduino_dataref_write(self, dataref: str, value: float) -> None:
        """Handle dataref write request from Arduino."""
        if self.xplane_conn.connected:
            task = asyncio.create_task(self.xplane_conn.write_dataref(dataref, value))
            # Store task to prevent garbage collection
            if not hasattr(self, "_active_tasks"):
                self._active_tasks = set()
            self._active_tasks.add(task)
            task.add_done_callback(lambda t: self._active_tasks.discard(t))

    def _on_arduino_command_send(self, command: str) -> None:
        """Handle command send request from Arduino."""
        if self.xplane_conn.connected:
            task = asyncio.create_task(self.xplane_conn.send_command(command))
            # Store task to prevent garbage collection
            if not hasattr(self, "_active_tasks"):
                self._active_tasks = set()
            self._active_tasks.add(task)
            task.add_done_callback(lambda t: self._active_tasks.discard(t))

    def _on_variable_update(self, name: str, value: float) -> None:
        """Handle variable update from the variable store."""
        # This is a notification callback - the store already has the updated value
        log.debug("Variable updated: %s = %.2f", name, value)

        # Update Output Panel tables
        if hasattr(self, "output_panel"):
            self.output_panel._on_variable_update(name, value)

    def _start_managers(self) -> None:
        """Start background managers."""
        self.hid_manager.start()
        log.info("Managers started")

    def _toggle_xplane_connection(self) -> None:
        """Toggle X-Plane connection."""
        task = asyncio.create_task(self._async_toggle_connection())
        # Store task to prevent garbage collection
        if not hasattr(self, "_active_tasks"):
            self._active_tasks = set()
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))

    async def _async_toggle_connection(self) -> None:
        """Async connection toggle."""
        if self.xplane_conn.connected:
            await self.xplane_conn.disconnect()
        else:
            # Get settings
            ip = self.settings_panel.get_xplane_ip()
            send_port = self.settings_panel.get_xplane_port()
            recv_port = self.settings_panel.get_recv_port()

            self.xplane_conn.ip = ip
            self.xplane_conn.port = send_port
            self.xplane_conn.recv_port = recv_port

            success = await self.xplane_conn.connect()

            if success:
                # Subscribe to condition datarefs from all mappings
                self._subscribe_condition_datarefs()

                # Perform immediate state sync
                task = asyncio.create_task(self.input_mapper.sync_hardware_to_xplane())
                # Store task to prevent garbage collection
                if not hasattr(self, "_active_tasks"):
                    self._active_tasks = set()
                self._active_tasks.add(task)
                task.add_done_callback(lambda t: self._active_tasks.discard(t))
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Failed to connect to X-Plane.\n\n"
                    f"Sending to: {ip}:{send_port}\n"
                    f"Receiving on port: {recv_port}\n\n"
                    "Make sure X-Plane is running.",
                )

    def _subscribe_condition_datarefs(self) -> None:
        """Subscribe to all datarefs used in conditions."""
        subscribed = set()

        for mapping in self.input_mapper.get_mappings():
            # Subscribe to all datarefs used in the new multi-condition system
            for rule in mapping.conditions:
                self._process_condition_rule(rule, subscribed)

    def _process_condition_rule(self, rule, subscribed_set):
        """Helper method to process individual condition rules."""
        if rule.enabled and rule.dataref and rule.dataref not in subscribed_set:
            self._create_and_track_task(
                self.xplane_conn.subscribe_dataref(rule.dataref, 5)
            )
            subscribed_set.add(rule.dataref)
            log.info("Subscribed to condition dataref: %s", rule.dataref)

    def _on_xplane_connection_changed(self, connected: bool) -> None:
        """Handle X-Plane connection state change."""
        if connected:
            self._handle_xplane_connected()
        else:
            self._handle_xplane_disconnected()

    def _handle_xplane_connected(self) -> None:
        """Handle X-Plane connection established."""
        self.xplane_status.setText("X-Plane: Connected")
        self.xplane_status.setStyleSheet("color: green; font-weight: bold;")
        self.connect_btn.setText("Disconnect")
        self.sync_btn.setEnabled(True)
        self.status_bar.showMessage("Connected to X-Plane")
        # Start logic engine when connected
        self._logic_timer.start(100)

        # Sync hardware switches to X-Plane immediately
        self._create_and_track_task(self.input_mapper.sync_hardware_to_xplane())

        # Sync initial values for variables/logic
        self._create_and_track_task(self.logic_engine.sync_initial_values())

        # Subscribe to aircraft ICAO for auto-profile switching
        for i in range(40):
            self._create_and_track_task(
                self.xplane_conn.subscribe_dataref(
                    f"sim/aircraft/view/acf_ICAO[{i}]", 1
                )
            )

    def _handle_xplane_disconnected(self) -> None:
        """Handle X-Plane disconnection."""
        self.xplane_status.setText("X-Plane: Disconnected")
        self.xplane_status.setStyleSheet("color: red; font-weight: bold;")
        self.connect_btn.setText("Connect to X-Plane")
        self.sync_btn.setEnabled(False)
        self.status_bar.showMessage("Disconnected from X-Plane")
        # Stop logic engine when disconnected
        self._logic_timer.stop()

    def _create_and_track_task(self, coro):
        """Helper method to create and track asyncio tasks to prevent garbage collection."""
        task = asyncio.create_task(coro)
        if not hasattr(self, "_active_tasks"):
            self._active_tasks = set()
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))
        return task

    # --- Search Help Refresh ---

    def refresh_search_helpers(self):
        """
        Notify all UI components that the pool of searchable IDs has changed.
        This updates the 'Completer' dropdowns without needing an app restart.
        """
        log.info("Refreshing search helpers across all panels...")

        # 1. Update the Dataref Manager's internal cache if needed (it usually fetches live)
        # But we ensure it's called so the UI pulls fresh lists.

        # 2. Refresh Output Panel (Subscribes search box)
        if hasattr(self, "output_panel"):
            self.output_panel.refresh_from_manager()

        # 3. Refresh Arduino Panel (Mappings search box)
        if hasattr(self, "arduino_panel"):
            if hasattr(self.arduino_panel, "refresh_from_manager"):
                self.arduino_panel.refresh_from_manager()

        # 4. Input Panels / Dialogs
        # These are often transient, but if they are open, we can't easily reach them
        # unless they registered themselves. However, most are recreated on demand.

    def _on_dataref_update(self, dataref: str, value: float) -> None:
        """Handle dataref update from X-Plane."""
        # Update Output Panel
        if hasattr(self, "output_panel"):
            self.output_panel.on_dataref_update(dataref, value)

        # Update Input Mapper state (for logic evaluation)
        if hasattr(self, "input_mapper"):
            self.input_mapper.on_dataref_update(dataref, value)

        # Forward to Arduino Manager (Universal Mappings handled inside manager now)
        if hasattr(self, "arduino_manager"):
            self.arduino_manager.on_dataref_update(dataref, value)

        # Update input mapper (for condition evaluation and toggle tracking)
        self.input_mapper.update_current_value(dataref, value)

        # Handle Aircraft Change detection
        if "sim/aircraft/view/acf_ICAO[" in dataref:
            self._handle_aircraft_icao_change(dataref, value)

    def _handle_aircraft_icao_change(self, dataref: str, value: float) -> None:
        """Handle aircraft ICAO change detection and auto-profile loading."""
        try:
            # Extract index
            idx = int(dataref.split("[")[1].split("]")[0])
            if 0 <= idx < 40:
                old_icao = self._current_icao
                self._icao_buffer[idx] = int(value)

                # Rebuild string
                chars = []
                for v in self._icao_buffer:
                    if v == 0:
                        break
                    chars.append(chr(v))
                new_icao = "".join(chars).strip()

                if new_icao and new_icao != old_icao:
                    self._current_icao = new_icao
                    log.info("Aircraft changed to: %s", new_icao)
                    if self._auto_profile_enabled:
                        self._auto_load_aircraft_profile(new_icao)
        except Exception as e:
            log.error("Error tracking aircraft ICAO: %s", e)

    def _auto_load_aircraft_profile(self, icao: str):
        """Try to load a profile for the current aircraft."""
        # Check if profile exists
        profile_path = self.profile_manager.PROFILE_DIR / f"{icao}.json"
        if profile_path.exists():
            log.info("Auto-loading profile for %s...", icao)
            self.profile_manager.load_profile(icao)
            self.output_panel.refresh_tables()
            self.status_bar.showMessage(f"Auto-loaded profile: {icao}")
        else:
            log.debug("No specific profile found for %s", icao)

    def _toggle_output_sync(self) -> None:
        """Handle 'Auto-Sync Output' button click."""
        # For now, we assume local host.
        # In the future, we could detect local IP or use discovered IP.
        local_ip = "127.0.0.1"
        local_port = self.xplane_conn.recv_port

        # Tell X-Plane to send data to us (ISE4)
        task = asyncio.create_task(
            self.xplane_conn.set_data_output_target(local_ip, local_port)
        )
        # Store task to prevent garbage collection
        if not hasattr(self, "_active_tasks"):
            self._active_tasks = set()
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))

        # Enable common interesting rows (DSEL)
        # 0=frame rate, 3=speeds, 4=G-load, 17=pitch/roll, 20=lat/lon
        task = asyncio.create_task(
            self.xplane_conn.select_data_output([0, 3, 4, 17, 20])
        )
        # Store task to prevent garbage collection
        if not hasattr(self, "_active_tasks"):
            self._active_tasks = set()
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))

        self.status_bar.showMessage("Sent Auto-Sync (ISE4/DSEL) to X-Plane")
        log.info("Sent Auto-Sync (ISE4 and DSEL) to X-Plane")

        QMessageBox.information(
            self,
            "Auto-Sync Sent",
            f"Sent commands to X-Plane:\n\n"
            f"1. Set Data Output target to {local_ip}:{local_port}\n"
            f"2. Enabled common data rows (speeds, position, etc.)\n\n"
            f"You should now start seeing values without ticking checkboxes manually.",
        )

    def _update_status(self) -> None:
        """Periodic status update."""
        # Count connected devices
        arduino_count = sum(
            1
            for d in self.arduino_manager.devices_snapshot().values()
            if d.is_connected
        )
        hid_count = sum(
            1 for d in self.hid_manager.devices_snapshot().values() if d.connected
        )

        parts = []
        if self.xplane_conn.connected:
            parts.append("X-Plane: OK")
        if arduino_count > 0:
            parts.append(f"Arduino: {arduino_count}")
        if hid_count > 0:
            parts.append(f"HID: {hid_count}")

        if parts:
            self.status_bar.showMessage(" | ".join(parts))

    def closeEvent(self, event) -> None:
        """Handle window close."""
        log.info("Shutting down...")

        # Save profile on exit
        self.profile_manager.save_profile("default")
        log.info("Saved default profile")

        # Disconnect X-Plane
        if self.xplane_conn.connected:
            task = asyncio.create_task(self.xplane_conn.disconnect())
            # Store task to prevent garbage collection
            if not hasattr(self, "_active_tasks"):
                self._active_tasks = set()
            self._active_tasks.add(task)
            task.add_done_callback(lambda t: self._active_tasks.discard(t))

        self.hid_manager.stop()
        self.arduino_manager.disconnect_all()

        event.accept()
