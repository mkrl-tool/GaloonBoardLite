from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QPushButton, QTabWidget, QWidget, QSpinBox, QComboBox, QMessageBox,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from ..config import AppConfig, save_config
from ..garoon_api import GaroonApiClient

class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("設定 - ガルーン行動予定表")
        self.setFixedSize(520, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # タブ1: ガルーン接続設定
        self.tabs.addTab(self._create_connection_tab(), "ガルーン接続")

        # タブ2: メンバー選択
        self.tabs.addTab(self._create_members_tab(), "表示メンバー")

        # タブ3: アプリ動作設定
        self.tabs.addTab(self._create_behavior_tab(), "動作設定")

        # 下部ボタンエリア
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("キャンセル")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("保存して適用")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.save_btn.clicked.connect(self.save_and_accept)
        btn_layout.addWidget(self.save_btn)

        main_layout.addLayout(btn_layout)

    def _create_connection_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # モックモード切替
        self.mock_mode_chk = QCheckBox("デモ（モック）モードを使用する（ガルーン未接続でも動作確認可能）")
        self.mock_mode_chk.setStyleSheet("font-weight: bold; color: #0369a1;")
        self.mock_mode_chk.toggled.connect(self._on_mock_mode_toggled)
        layout.addWidget(self.mock_mode_chk)

        # 接続情報グループ
        conn_group = QGroupBox("ガルーン パッケージ版 / クラウド版 接続設定")
        form = QFormLayout(conn_group)
        form.setSpacing(10)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("例: http://192.168.1.100/cgi-bin/cbgrn/grn.cgi")
        form.addRow("ガルーン URL:", self.url_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("ガルーンのログイン名")
        form.addRow("ログイン名:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("ガルーンのパスワード")
        form.addRow("パスワード:", self.password_edit)

        # SSL検証
        self.verify_ssl_chk = QCheckBox("SSL証明書を検証する（自己署名・社内オレオレ証明書の場合はチェックを外す）")
        form.addRow("", self.verify_ssl_chk)

        # Basic認証
        self.basic_auth_chk = QCheckBox("WebサーバーのBasic認証を使用する")
        self.basic_auth_chk.toggled.connect(self._on_basic_auth_toggled)
        form.addRow("", self.basic_auth_chk)

        self.basic_user_edit = QLineEdit()
        self.basic_user_edit.setPlaceholderText("Basic認証 ユーザー名")
        form.addRow("Basic ユーザー:", self.basic_user_edit)

        self.basic_pass_edit = QLineEdit()
        self.basic_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.basic_pass_edit.setPlaceholderText("Basic認証 パスワード")
        form.addRow("Basic パスワード:", self.basic_pass_edit)

        layout.addWidget(conn_group)

        # 接続テストボタン
        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("🔌 接続テストを実行")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.test_btn.clicked.connect(self.run_connection_test)
        test_layout.addWidget(self.test_btn)

        self.test_result_lbl = QLabel("")
        self.test_result_lbl.setWordWrap(True)
        test_layout.addWidget(self.test_result_lbl, 1)

        layout.addLayout(test_layout)
        layout.addStretch()

        return widget

    def _create_members_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        desc_lbl = QLabel("予定表に表示するメンバーを選択または指定します。")
        desc_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(desc_lbl)

        # ガルーンから取得ボタン
        fetch_layout = QHBoxLayout()
        self.fetch_users_btn = QPushButton("👥 ガルーンからユーザー一覧を取得")
        self.fetch_users_btn.clicked.connect(self.fetch_users_from_garoon)
        fetch_layout.addWidget(self.fetch_users_btn)

        self.select_all_btn = QPushButton("全選択")
        self.select_all_btn.clicked.connect(lambda: self._set_all_members_checked(True))
        fetch_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("全解除")
        self.deselect_all_btn.clicked.connect(lambda: self._set_all_members_checked(False))
        fetch_layout.addWidget(self.deselect_all_btn)

        layout.addLayout(fetch_layout)

        # ユーザー選択リスト
        self.users_list_widget = QListWidget()
        layout.addWidget(self.users_list_widget)

        # 手動ID指定
        manual_group = QGroupBox("ユーザーIDの手動指定（カンマ区切り）")
        manual_layout = QVBoxLayout(manual_group)
        self.manual_ids_edit = QLineEdit()
        self.manual_ids_edit.setPlaceholderText("例: 1, 2, 5, 8 (空欄の場合は上のリスト選択または全員)")
        manual_layout.addWidget(self.manual_ids_edit)
        layout.addWidget(manual_group)

        return widget

    def _create_behavior_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        # 更新間隔
        self.interval_combo = QComboBox()
        self.interval_combo.addItems([
            "1分ごと", "3分ごと（推奨）", "5分ごと", "10分ごと", "15分ごと", "30分ごと", "手動更新のみ"
        ])
        form.addRow("自動更新間隔:", self.interval_combo)

        # 最前面ピン留め
        self.always_top_chk = QCheckBox("常に最前面に表示する（ピン留め）")
        form.addRow("", self.always_top_chk)

        # 最小化時にトレイへ
        self.min_tray_chk = QCheckBox("最小化時にタスクトレイに格納する")
        form.addRow("", self.min_tray_chk)

        # 閉じるボタンでトレイへ
        self.close_tray_chk = QCheckBox("「×」ボタンを押したときに終了せずタスクトレイに常駐する")
        form.addRow("", self.close_tray_chk)

        layout.addLayout(form)
        layout.addStretch()

        return widget

    def load_settings(self):
        # 接続
        self.url_edit.setText(self.config.garoon_url)
        self.username_edit.setText(self.config.username)
        self.password_edit.setText(self.config.password)
        self.verify_ssl_chk.setChecked(self.config.verify_ssl)
        self.basic_auth_chk.setChecked(self.config.use_basic_auth)
        self.basic_user_edit.setText(self.config.basic_username)
        self.basic_pass_edit.setText(self.config.basic_password)
        self.mock_mode_chk.setChecked(self.config.mock_mode)

        self._on_basic_auth_toggled(self.config.use_basic_auth)

        # 動作設定
        interval_map = {1: 0, 3: 1, 5: 2, 10: 3, 15: 4, 30: 5, 0: 6}
        idx = interval_map.get(self.config.refresh_interval_minutes, 1)
        self.interval_combo.setCurrentIndex(idx)

        self.always_top_chk.setChecked(self.config.always_on_top)
        self.min_tray_chk.setChecked(self.config.minimize_to_tray)
        self.close_tray_chk.setChecked(self.config.close_to_tray)

        # メンバー手動ID
        if self.config.target_user_ids:
            self.manual_ids_edit.setText(", ".join(self.config.target_user_ids))

        # 初期ユーザー一覧を読み込み
        self.fetch_users_from_garoon()

    def _on_mock_mode_toggled(self, checked: bool):
        if checked:
            self.test_result_lbl.setText("💡 デモモードが有効です（API通信は行われません）")
            self.test_result_lbl.setStyleSheet("color: #0369a1;")
        else:
            self.test_result_lbl.setText("")

    def _on_basic_auth_toggled(self, checked: bool):
        self.basic_user_edit.setEnabled(checked)
        self.basic_pass_edit.setEnabled(checked)

    def _set_all_members_checked(self, checked: bool):
        for i in range(self.users_list_widget.count()):
            item = self.users_list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def run_connection_test(self):
        temp_cfg = self._get_current_input_config()
        client = GaroonApiClient(temp_cfg)
        self.test_btn.setEnabled(False)
        self.test_btn.setText("テスト中...")

        ok, msg = client.test_connection()
        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔌 接続テストを実行")

        if ok:
            self.test_result_lbl.setText(f"✅ {msg}")
            self.test_result_lbl.setStyleSheet("color: #16a34a; font-weight: bold;")
        else:
            self.test_result_lbl.setText(f"❌ {msg}")
            self.test_result_lbl.setStyleSheet("color: #dc2626;")

    def fetch_users_from_garoon(self):
        temp_cfg = self._get_current_input_config()
        client = GaroonApiClient(temp_cfg)
        users = client.get_users()

        self.users_list_widget.clear()
        target_set = set(self.config.target_user_ids)

        for u in users:
            item = QListWidgetItem(f"{u.name} (ID: {u.id})")
            item.setData(Qt.ItemDataRole.UserRole, u.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # 既に設定されていればチェック、初回空の場合は全チェック
            if not target_set or u.id in target_set:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            self.users_list_widget.addItem(item)

    def _get_current_input_config(self) -> AppConfig:
        cfg = AppConfig()
        cfg.garoon_url = self.url_edit.text().strip()
        cfg.username = self.username_edit.text().strip()
        cfg.password = self.password_edit.text()
        cfg.verify_ssl = self.verify_ssl_chk.isChecked()
        cfg.use_basic_auth = self.basic_auth_chk.isChecked()
        cfg.basic_username = self.basic_user_edit.text().strip()
        cfg.basic_password = self.basic_pass_edit.text()
        cfg.mock_mode = self.mock_mode_chk.isChecked()
        return cfg

    def save_and_accept(self):
        # 接続設定
        self.config.garoon_url = self.url_edit.text().strip()
        self.config.username = self.username_edit.text().strip()
        self.config.password = self.password_edit.text()
        self.config.verify_ssl = self.verify_ssl_chk.isChecked()
        self.config.use_basic_auth = self.basic_auth_chk.isChecked()
        self.config.basic_username = self.basic_user_edit.text().strip()
        self.config.basic_password = self.basic_pass_edit.text()
        self.config.mock_mode = self.mock_mode_chk.isChecked()

        # 動作設定
        interval_values = [1, 3, 5, 10, 15, 30, 0]
        self.config.refresh_interval_minutes = interval_values[self.interval_combo.currentIndex()]
        self.config.always_on_top = self.always_top_chk.isChecked()
        self.config.minimize_to_tray = self.min_tray_chk.isChecked()
        self.config.close_to_tray = self.close_tray_chk.isChecked()

        # メンバー設定
        manual_ids = [s.strip() for s in self.manual_ids_edit.text().split(",") if s.strip()]
        if manual_ids:
            self.config.target_user_ids = manual_ids
        else:
            selected_ids = []
            for i in range(self.users_list_widget.count()):
                item = self.users_list_widget.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    selected_ids.append(item.data(Qt.ItemDataRole.UserRole))
            self.config.target_user_ids = selected_ids

        save_config(self.config)
        self.accept()
