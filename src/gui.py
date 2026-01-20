"""PyQt6 GUI for osu! Beatmap Downloader."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QGroupBox, QCheckBox,
    QMessageBox, QFileDialog, QHeaderView, QAbstractItemView, QStatusBar,
    QDialog, QDialogButtonBox, QFormLayout, QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

from typing import List, Optional
from dataclasses import dataclass

from .api_client import OsuMode, SearchFilters, BeatmapInfo
from .downloader import DownloadTask, DownloadStatus


# osu! themed colors
OSU_PINK = "#FF66AB"
OSU_PURPLE = "#8866EE"
OSU_DARK_BG = "#1a1a2e"
OSU_DARKER_BG = "#16162a"
OSU_LIGHT_TEXT = "#ffffff"
OSU_MUTED_TEXT = "#888899"


def get_dark_stylesheet() -> str:
    """Get the dark theme stylesheet with osu! colors."""
    return f"""
        QMainWindow, QDialog {{
            background-color: {OSU_DARK_BG};
        }}

        QWidget {{
            background-color: {OSU_DARK_BG};
            color: {OSU_LIGHT_TEXT};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}

        QGroupBox {{
            border: 2px solid {OSU_PURPLE};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 10px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: {OSU_PINK};
        }}

        QLabel {{
            color: {OSU_LIGHT_TEXT};
        }}

        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {OSU_DARKER_BG};
            border: 1px solid {OSU_PURPLE};
            border-radius: 4px;
            padding: 6px;
            color: {OSU_LIGHT_TEXT};
            min-height: 20px;
        }}

        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border: 2px solid {OSU_PINK};
        }}

        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {OSU_PINK};
        }}

        QComboBox QAbstractItemView {{
            background-color: {OSU_DARKER_BG};
            border: 1px solid {OSU_PURPLE};
            selection-background-color: {OSU_PURPLE};
        }}

        QPushButton {{
            background-color: {OSU_PURPLE};
            color: {OSU_LIGHT_TEXT};
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
            min-height: 20px;
        }}

        QPushButton:hover {{
            background-color: {OSU_PINK};
        }}

        QPushButton:pressed {{
            background-color: #cc5599;
        }}

        QPushButton:disabled {{
            background-color: #444466;
            color: #888899;
        }}

        QPushButton#cancelBtn {{
            background-color: #cc4444;
        }}

        QPushButton#cancelBtn:hover {{
            background-color: #ff5555;
        }}

        QTableWidget {{
            background-color: {OSU_DARKER_BG};
            alternate-background-color: #1e1e3a;
            border: 1px solid {OSU_PURPLE};
            border-radius: 4px;
            gridline-color: #333355;
        }}

        QTableWidget::item {{
            padding: 5px;
        }}

        QTableWidget::item:selected {{
            background-color: {OSU_PURPLE};
        }}

        QHeaderView::section {{
            background-color: #252550;
            color: {OSU_PINK};
            padding: 8px;
            border: none;
            border-bottom: 2px solid {OSU_PURPLE};
            font-weight: bold;
        }}

        QProgressBar {{
            border: 1px solid {OSU_PURPLE};
            border-radius: 4px;
            background-color: {OSU_DARKER_BG};
            text-align: center;
            color: {OSU_LIGHT_TEXT};
        }}

        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {OSU_PURPLE}, stop:1 {OSU_PINK});
            border-radius: 3px;
        }}

        QStatusBar {{
            background-color: {OSU_DARKER_BG};
            color: {OSU_MUTED_TEXT};
        }}

        QCheckBox {{
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {OSU_PURPLE};
            border-radius: 4px;
            background-color: {OSU_DARKER_BG};
        }}

        QCheckBox::indicator:checked {{
            background-color: {OSU_PINK};
            border-color: {OSU_PINK};
        }}

        QTabWidget::pane {{
            border: 1px solid {OSU_PURPLE};
            border-radius: 4px;
        }}

        QTabBar::tab {{
            background-color: {OSU_DARKER_BG};
            color: {OSU_MUTED_TEXT};
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}

        QTabBar::tab:selected {{
            background-color: {OSU_PURPLE};
            color: {OSU_LIGHT_TEXT};
        }}

        QScrollBar:vertical {{
            background-color: {OSU_DARKER_BG};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {OSU_PURPLE};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {OSU_PINK};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QTextEdit {{
            background-color: {OSU_DARKER_BG};
            border: 1px solid {OSU_PURPLE};
            border-radius: 4px;
            color: {OSU_LIGHT_TEXT};
        }}
    """


class ConfigDialog(QDialog):
    """Dialog for configuring OAuth credentials."""

    def __init__(self, parent=None, client_id: int = 0, client_secret: str = ""):
        super().__init__(parent)
        self.setWindowTitle("osu! API Configuration")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Enter your osu! OAuth credentials.\n"
            "Get them from: https://osu.ppy.sh/home/account/edit#oauth"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {OSU_MUTED_TEXT}; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # Form
        form_layout = QFormLayout()

        self.client_id_input = QSpinBox()
        self.client_id_input.setRange(0, 999999999)
        self.client_id_input.setValue(client_id)
        form_layout.addRow("Client ID:", self.client_id_input)

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setText(client_secret)
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Client Secret:", self.client_secret_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_credentials(self) -> tuple[int, str]:
        """Get the entered credentials."""
        return self.client_id_input.value(), self.client_secret_input.text()


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals for thread-safe UI updates
    search_complete = pyqtSignal(list)
    search_error = pyqtSignal(str)
    pp_calculated = pyqtSignal(int, float)  # beatmap_id, pp
    download_progress = pyqtSignal(object)  # DownloadTask
    batch_progress = pyqtSignal(int, int)  # completed, total
    status_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("osu! Beatmap Downloader")
        self.setMinimumSize(1200, 800)

        # Apply dark theme
        self.setStyleSheet(get_dark_stylesheet())

        # Store search results
        self.search_results: List[BeatmapInfo] = []
        self.filtered_results: List[BeatmapInfo] = []

        # Setup UI
        self._setup_ui()

        # Connect signals
        self.search_complete.connect(self._on_search_complete)
        self.search_error.connect(self._on_search_error)
        self.pp_calculated.connect(self._on_pp_calculated)
        self.download_progress.connect(self._on_download_progress)
        self.batch_progress.connect(self._on_batch_progress)
        self.status_update.connect(self._on_status_update)

    def _setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("osu! Beatmap Downloader")
        title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {OSU_PINK};
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Top section: Filters
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(15)

        # Mode selection group
        mode_group = QGroupBox("Game Mode")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "osu! Standard",
            "osu! Taiko",
            "osu! Catch",
            "osu! Mania"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        # Mania keys selector (hidden by default)
        self.mania_keys_widget = QWidget()
        mania_keys_layout = QHBoxLayout(self.mania_keys_widget)
        mania_keys_layout.setContentsMargins(0, 0, 0, 0)
        mania_keys_layout.addWidget(QLabel("Keys:"))
        self.mania_keys_combo = QComboBox()
        self.mania_keys_combo.addItems(["Any", "4K", "7K"])
        mania_keys_layout.addWidget(self.mania_keys_combo)
        self.mania_keys_widget.hide()
        mode_layout.addWidget(self.mania_keys_widget)

        filters_layout.addWidget(mode_group)

        # Star rating group
        star_group = QGroupBox("Star Rating")
        star_layout = QGridLayout(star_group)

        star_layout.addWidget(QLabel("Min:"), 0, 0)
        self.min_stars = QDoubleSpinBox()
        self.min_stars.setRange(0, 15)
        self.min_stars.setValue(0)
        self.min_stars.setSingleStep(0.5)
        self.min_stars.setDecimals(2)
        star_layout.addWidget(self.min_stars, 0, 1)

        star_layout.addWidget(QLabel("Max:"), 1, 0)
        self.max_stars = QDoubleSpinBox()
        self.max_stars.setRange(0, 15)
        self.max_stars.setValue(10)
        self.max_stars.setSingleStep(0.5)
        self.max_stars.setDecimals(2)
        star_layout.addWidget(self.max_stars, 1, 1)

        filters_layout.addWidget(star_group)

        # PP filter group
        pp_group = QGroupBox("PP Filter (100% SS)")
        pp_layout = QGridLayout(pp_group)

        pp_layout.addWidget(QLabel("Min:"), 0, 0)
        self.min_pp = QSpinBox()
        self.min_pp.setRange(0, 10000)
        self.min_pp.setValue(0)
        pp_layout.addWidget(self.min_pp, 0, 1)

        pp_layout.addWidget(QLabel("Max:"), 1, 0)
        self.max_pp = QSpinBox()
        self.max_pp.setRange(0, 10000)
        self.max_pp.setValue(10000)
        pp_layout.addWidget(self.max_pp, 1, 1)

        filters_layout.addWidget(pp_group)

        # Length filter group
        length_group = QGroupBox("Length (seconds)")
        length_layout = QGridLayout(length_group)

        length_layout.addWidget(QLabel("Min:"), 0, 0)
        self.min_length = QSpinBox()
        self.min_length.setRange(0, 3600)
        self.min_length.setValue(0)
        length_layout.addWidget(self.min_length, 0, 1)

        length_layout.addWidget(QLabel("Max:"), 1, 0)
        self.max_length = QSpinBox()
        self.max_length.setRange(0, 3600)
        self.max_length.setValue(600)
        length_layout.addWidget(self.max_length, 1, 1)

        filters_layout.addWidget(length_group)

        # BPM filter group
        bpm_group = QGroupBox("BPM Range")
        bpm_layout = QGridLayout(bpm_group)

        bpm_layout.addWidget(QLabel("Min:"), 0, 0)
        self.min_bpm = QSpinBox()
        self.min_bpm.setRange(0, 500)
        self.min_bpm.setValue(0)
        bpm_layout.addWidget(self.min_bpm, 0, 1)

        bpm_layout.addWidget(QLabel("Max:"), 1, 0)
        self.max_bpm = QSpinBox()
        self.max_bpm.setRange(0, 500)
        self.max_bpm.setValue(500)
        bpm_layout.addWidget(self.max_bpm, 1, 1)

        filters_layout.addWidget(bpm_group)

        # Search options group
        search_group = QGroupBox("Search Options")
        search_layout = QGridLayout(search_group)

        search_layout.addWidget(QLabel("Max Results:"), 0, 0)
        self.max_results = QSpinBox()
        self.max_results.setRange(1, 500)
        self.max_results.setValue(50)
        search_layout.addWidget(self.max_results, 0, 1)

        filters_layout.addWidget(search_group)

        main_layout.addLayout(filters_layout)

        # Search button row
        search_row = QHBoxLayout()

        self.search_btn = QPushButton("Search Beatmaps")
        self.search_btn.setMinimumWidth(200)
        self.search_btn.clicked.connect(self._on_search_clicked)
        search_row.addWidget(self.search_btn)

        self.config_btn = QPushButton("Configure API")
        self.config_btn.clicked.connect(self._on_config_clicked)
        search_row.addWidget(self.config_btn)

        search_row.addStretch()

        main_layout.addLayout(search_row)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Search progress
        search_progress_layout = QHBoxLayout()
        search_progress_layout.addWidget(QLabel("Search/PP Calculation:"))
        self.search_progress = QProgressBar()
        self.search_progress.setTextVisible(True)
        self.search_progress.setFormat("%v / %m maps")
        search_progress_layout.addWidget(self.search_progress)
        progress_layout.addLayout(search_progress_layout)

        # Download progress
        download_progress_layout = QHBoxLayout()
        download_progress_layout.addWidget(QLabel("Downloads:"))
        self.download_progress_bar = QProgressBar()
        self.download_progress_bar.setTextVisible(True)
        self.download_progress_bar.setFormat("%v / %m beatmaps")
        download_progress_layout.addWidget(self.download_progress_bar)
        progress_layout.addLayout(download_progress_layout)

        main_layout.addWidget(progress_group)

        # Results table
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(9)
        self.results_table.setHorizontalHeaderLabels([
            "Select", "Title", "Difficulty", "Mode", "Stars",
            "PP (SS)", "Length", "BPM", "Creator"
        ])

        # Configure table
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSortingEnabled(True)

        results_layout.addWidget(self.results_table)

        # Selection controls
        selection_row = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        selection_row.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        selection_row.addWidget(self.deselect_all_btn)

        selection_row.addStretch()

        self.selected_count_label = QLabel("0 beatmaps selected")
        self.selected_count_label.setStyleSheet(f"color: {OSU_MUTED_TEXT};")
        selection_row.addWidget(self.selected_count_label)

        results_layout.addLayout(selection_row)

        main_layout.addWidget(results_group)

        # Download controls
        download_row = QHBoxLayout()

        self.download_btn = QPushButton("Download Selected")
        self.download_btn.setMinimumWidth(200)
        self.download_btn.clicked.connect(self._on_download_clicked)
        download_row.addWidget(self.download_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setEnabled(False)
        download_row.addWidget(self.cancel_btn)

        download_row.addStretch()

        self.open_folder_btn = QPushButton("Open Downloads Folder")
        self.open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        download_row.addWidget(self.open_folder_btn)

        main_layout.addLayout(download_row)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Configure API credentials to start.")

    def _on_mode_changed(self, index: int):
        """Handle mode selection change."""
        # Show/hide mania keys selector
        self.mania_keys_widget.setVisible(index == 3)  # Mania mode

    def _on_config_clicked(self):
        """Handle config button click."""
        # This will be connected to the main app
        pass

    def _on_search_clicked(self):
        """Handle search button click."""
        # This will be connected to the main app
        pass

    def _on_download_clicked(self):
        """Handle download button click."""
        # This will be connected to the main app
        pass

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        # This will be connected to the main app
        pass

    def _on_open_folder_clicked(self):
        """Handle open folder button click."""
        # This will be connected to the main app
        pass

    def _select_all(self):
        """Select all beatmaps."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
        self._update_selection_count()

    def _deselect_all(self):
        """Deselect all beatmaps."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
        self._update_selection_count()

    def _update_selection_count(self):
        """Update the selection count label."""
        count = self.get_selected_count()
        self.selected_count_label.setText(f"{count} beatmaps selected")

    def get_selected_count(self) -> int:
        """Get the number of selected beatmaps."""
        count = 0
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                count += 1
        return count

    def get_selected_beatmaps(self) -> List[BeatmapInfo]:
        """Get list of selected beatmaps."""
        selected = []
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                if row < len(self.filtered_results):
                    selected.append(self.filtered_results[row])
        return selected

    def get_search_filters(self) -> SearchFilters:
        """Get current search filters from UI."""
        mode_index = self.mode_combo.currentIndex()
        mode = OsuMode(mode_index)

        mania_keys = None
        if mode == OsuMode.MANIA:
            keys_text = self.mania_keys_combo.currentText()
            if keys_text == "4K":
                mania_keys = 4
            elif keys_text == "7K":
                mania_keys = 7

        return SearchFilters(
            mode=mode,
            min_stars=self.min_stars.value(),
            max_stars=self.max_stars.value(),
            min_length=self.min_length.value(),
            max_length=self.max_length.value(),
            min_bpm=self.min_bpm.value(),
            max_bpm=self.max_bpm.value(),
            mania_keys=mania_keys
        )

    def get_pp_range(self) -> tuple[int, int]:
        """Get PP filter range."""
        return self.min_pp.value(), self.max_pp.value()

    def get_max_results(self) -> int:
        """Get max results setting."""
        return self.max_results.value()

    def set_searching(self, searching: bool):
        """Set UI state for searching."""
        self.search_btn.setEnabled(not searching)
        self.download_btn.setEnabled(not searching)
        self.cancel_btn.setEnabled(searching)

        if searching:
            self.search_progress.setValue(0)
            self.status_bar.showMessage("Searching...")

    def set_downloading(self, downloading: bool):
        """Set UI state for downloading."""
        self.search_btn.setEnabled(not downloading)
        self.download_btn.setEnabled(not downloading)
        self.cancel_btn.setEnabled(downloading)

        if downloading:
            self.download_progress_bar.setValue(0)
            self.status_bar.showMessage("Downloading...")

    def populate_results(self, beatmaps: List[BeatmapInfo]):
        """Populate the results table with beatmaps."""
        self.filtered_results = beatmaps
        self.results_table.setRowCount(len(beatmaps))

        for row, beatmap in enumerate(beatmaps):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_selection_count)
            self.results_table.setCellWidget(row, 0, checkbox)

            # Title (artist - title)
            title_item = QTableWidgetItem(f"{beatmap.artist} - {beatmap.title}")
            title_item.setToolTip(beatmap.display_name)
            self.results_table.setItem(row, 1, title_item)

            # Difficulty name
            diff_item = QTableWidgetItem(beatmap.version)
            self.results_table.setItem(row, 2, diff_item)

            # Mode
            mode_names = ["Standard", "Taiko", "Catch", "Mania"]
            mode_item = QTableWidgetItem(mode_names[beatmap.mode.value])
            self.results_table.setItem(row, 3, mode_item)

            # Stars
            stars_item = QTableWidgetItem(f"{beatmap.stars:.2f}*")
            stars_item.setData(Qt.ItemDataRole.UserRole, beatmap.stars)
            self.results_table.setItem(row, 4, stars_item)

            # PP (will be filled in later)
            pp_text = f"{beatmap.calculated_pp:.0f}" if beatmap.calculated_pp else "..."
            pp_item = QTableWidgetItem(pp_text)
            pp_item.setData(Qt.ItemDataRole.UserRole, beatmap.calculated_pp or 0)
            self.results_table.setItem(row, 5, pp_item)

            # Length
            length_item = QTableWidgetItem(beatmap.formatted_length)
            length_item.setData(Qt.ItemDataRole.UserRole, beatmap.length)
            self.results_table.setItem(row, 6, length_item)

            # BPM
            bpm_item = QTableWidgetItem(f"{beatmap.bpm:.0f}")
            bpm_item.setData(Qt.ItemDataRole.UserRole, beatmap.bpm)
            self.results_table.setItem(row, 7, bpm_item)

            # Creator
            creator_item = QTableWidgetItem(beatmap.creator)
            self.results_table.setItem(row, 8, creator_item)

        self._update_selection_count()

    def update_pp_value(self, row: int, pp: float):
        """Update PP value for a specific row."""
        if row < self.results_table.rowCount():
            pp_item = QTableWidgetItem(f"{pp:.0f}")
            pp_item.setData(Qt.ItemDataRole.UserRole, pp)
            self.results_table.setItem(row, 5, pp_item)

    def _on_search_complete(self, beatmaps: List[BeatmapInfo]):
        """Handle search completion."""
        self.search_results = beatmaps
        self.populate_results(beatmaps)
        self.set_searching(False)
        self.status_bar.showMessage(f"Found {len(beatmaps)} beatmaps")

    def _on_search_error(self, error: str):
        """Handle search error."""
        self.set_searching(False)
        QMessageBox.critical(self, "Search Error", error)
        self.status_bar.showMessage("Search failed")

    def _on_pp_calculated(self, beatmap_id: int, pp: float):
        """Handle PP calculation result."""
        # Find the row with this beatmap ID and update PP
        for row in range(self.results_table.rowCount()):
            if row < len(self.filtered_results):
                if self.filtered_results[row].beatmap_id == beatmap_id:
                    self.update_pp_value(row, pp)
                    self.filtered_results[row].calculated_pp = pp
                    break

    def _on_download_progress(self, task: DownloadTask):
        """Handle download progress update."""
        # Update status bar with current download
        if task.status == DownloadStatus.DOWNLOADING:
            self.status_bar.showMessage(
                f"Downloading: {task.title} ({task.progress:.0f}%)"
            )
        elif task.status == DownloadStatus.COMPLETED:
            self.status_bar.showMessage(f"Completed: {task.title}")
        elif task.status == DownloadStatus.FAILED:
            self.status_bar.showMessage(f"Failed: {task.title} - {task.error}")

    def _on_batch_progress(self, completed: int, total: int):
        """Handle batch download progress."""
        self.download_progress_bar.setMaximum(total)
        self.download_progress_bar.setValue(completed)

        if completed == total:
            self.set_downloading(False)
            self.status_bar.showMessage(f"Downloaded {completed} beatmaps")

    def _on_status_update(self, message: str):
        """Handle status update."""
        self.status_bar.showMessage(message)
