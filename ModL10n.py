# -*- coding: utf-8 -*-
#
# ModL10n
# Version: 5.0
#
# Description:
# A desktop application for semi-automatically translating Minecraft mods
# into Japanese using the Google Gemini API. It streamlines the translation
# process by handling mod scanning, diff-based translation, data merging,
# and resource pack generation.
#

import sys
import json
import re
import math
import zipfile
import datetime
import subprocess
import os
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTextEdit, QLabel,
                             QMessageBox, QGroupBox, QComboBox, QListWidget,
                             QListWidgetItem, QProgressBar, QGraphicsDropShadowEffect,
                             QCompleter, QListView)
from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt, QTimer
from PyQt5.QtGui import QFont, QColor

# 外部ライブラリのインポート
try:
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
except ImportError:
    print("必要なライブラリがインストールされていません。", file=sys.stderr)
    print("pip install google-generativeai", file=sys.stderr)
    sys.exit(1)


# --- スタイルシート(QSS) ---
FINAL_STYLE = """
QWidget {
    color: #d1d1d1;
    font-size: 10pt;
}
QWidget#main_widget {
    background-color: #1e2228;
}
QGroupBox {
    background-color: #282c34;
    border: 1px solid #3a3f4c;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
    font-size: 11pt;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    left: 10px;
    color: #c3c8d8;
}
QLabel#header_title {
    font-size: 24pt;
    font-weight: 900;
    font-family: "Segoe UI Black", "Arial Black", sans-serif;
    letter-spacing: 1px;
    color: #2267d6;
    padding: 0px 0 10px 0;
}
QLabel {
    color: #c3c8d8;
}
QLineEdit, QComboBox, QTextEdit, QListWidget {
    background-color: #21252b;
    border: 1px solid #3a3f4c;
    border-radius: 4px;
    padding: 8px;
    color: #d1d1d1;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2267d6;
}
QComboBox QAbstractItemView {
    background-color: #21252b;
    border: 1px solid #3a3f4c;
    color: #d1d1d1;
    selection-background-color: #2267d6;
    selection-color: #ffffff;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 24px;
}
QPushButton {
    background-color: #2c313a;
    border: 1px solid #3a3f4c;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 9pt;
}
QPushButton:hover {
    background-color: #3a3f4c;
    border-color: #5c6270;
}
QPushButton:pressed {
    background-color: #21252b;
}
QPushButton#small_btn {
    padding: 4px 10px;
    font-size: 9pt;
    background-color: #2c313a;
}
QPushButton#small_btn:hover {
    background-color: #3a3f4c;
}
QPushButton#run_btn {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b79eb, stop:1 #2267d6);
    border: 1px solid #1a52ab;
    border-radius: 6px;
    padding: 12px;
    font-size: 12pt;
    font-weight: bold;
    color: #ffffff;
}
QPushButton#run_btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3c86f0, stop:1 #2873ed);
    border: 1px solid #2267d6;
}
QPushButton#run_btn:pressed {
    background-color: #1a52ab;
}
QPushButton#run_btn:disabled {
    background-color: #5c6270;
    border: 1px solid #5c6270;
    color: #a0a0a0;
}
QTextEdit, QListWidget {
    font-family: "Consolas", "Courier New", monospace;
}
QTextEdit#log_area {
    border: none;
    padding: 10px;
}
QScrollBar:vertical {
    border: none;
    background: #21252b;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #4b5363;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #5c6270;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    border: none;
    background: #21252b;
    height: 8px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #4b5363;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #5c6270;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #21252b;
    height: 12px;
    margin-top: 5px;
    margin-bottom: 5px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2267d6, stop:1 #2ecc71);
    border-radius: 3px;
}
QLabel#api_status_valid { color: #2ecc71; }
QLabel#api_status_invalid { color: #e74c3c; }
QLabel#api_status_checking { color: #f39c12; }

/* --- コンソール用入力欄のスタイル --- */
QLineEdit#console_input {
    background-color: #1a1e24;
    border: none;
    border-radius: 6px;
    padding: 10px;
    color: #2b79eb;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11pt;
}
QLineEdit#console_input:focus {
    border: 1px solid #2267d6; 
    background-color: #1e2228;
}

/* --- サジェストリストのスタイル --- */
QListView#completer_list {
    background-color: #21252b;
    border: none;
    border-radius: 4px;
    color: #2b79eb;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11pt;
    outline: none;
}
QListView#completer_list::item {
    padding: 8px;
}
QListView#completer_list::item:hover, QListView#completer_list::item:selected {
    background-color: #2c313a;
    color: #2267d6;
}
"""

# --- 定数定義 ---
APP_VERSION = "5.0"
CONFIG_FILE_NAME = "config.json"
INPUT_DIR_NAME = "input"
OUTPUT_DIR_NAME = "output"
DELETED_ENTRY_FILE_NAME = "deleted_entry.json"


# --- 汎用ユーティリティ関数 ---
def load_json_file(path: Path) -> dict:
    """指定されたパスからJSONファイルを読み込み、辞書として返す。"""
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"JSON読み込みエラー ({path.name}): {e}", file=sys.stderr)
        return {}

def save_json_file(path: Path, data: dict) -> bool:
    """辞書データを指定されたパスにJSON形式で保存する。"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
        return True
    except Exception as e:
        print(f"JSON保存エラー ({path.name}): {e}", file=sys.stderr)
        return False

def load_env(filepath: str = ".env") -> dict:
    """.envファイルから環境変数を読み込む。"""
    env_data = {}
    path = Path(filepath)
    if not path.exists():
        return env_data
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()
    except Exception as e:
        print(f".envファイルの読み込み中にエラーが発生しました: {e}", file=sys.stderr)
    return env_data

def save_env(key: str, value: str, filepath: str = ".env"):
    """.envファイルに環境変数を保存する。"""
    env_data = load_env(filepath)
    env_data[key] = value
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for k, v in env_data.items():
                f.write(f"{k}={v}\n")
    except Exception as e:
        print(f".envファイルの保存中にエラーが発生しました: {e}", file=sys.stderr)


# --- 管理クラス ---
class ConfigManager:
    """設定ファイル(config.json)の読み書きを管理するクラス。"""
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.default_config = {
            "minecraft_version": "1.21",
            "glossary": {},
            "system_prompt": "以下のJSON形式のMinecraft Modの言語データを日本語に翻訳してください。キーは変更せず、値のみを自然な日本語に翻訳してください。\n\n{json_to_translate}"
        }

    def load_config(self) -> dict:
        loaded_config = load_json_file(self.config_path)
        config = self.default_config.copy()
        config.update(loaded_config)
        return config

    def save_config(self, config_data: dict):
        save_json_file(self.config_path, config_data)


class DeletedEntryManager:
    """過去に削除された翻訳キーの履歴(deleted_entry.json)を管理するクラス。"""
    def __init__(self, filepath: Path = Path(DELETED_ENTRY_FILE_NAME)):
        self.filepath = filepath
        self.entries = load_json_file(self.filepath)

    def save(self):
        save_json_file(self.filepath, self.entries)

    def add_deleted_keys(self, mod_id: str, keys_dict: dict):
        if not keys_dict:
            return
        if mod_id not in self.entries:
            self.entries[mod_id] = {}
        self.entries[mod_id].update(keys_dict)


# --- ワーカークラス ---
class ApiKeyValidator(QObject):
    """APIキーの有効性をバックグラウンドで検証するワーカー。"""
    validation_finished = pyqtSignal(bool, str)

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    def run(self):
        if not self.api_key:
            self.validation_finished.emit(False, self.api_key)
            return
        try:
            genai.configure(api_key=self.api_key)
            list(genai.list_models())
            self.validation_finished.emit(True, self.api_key)
        except Exception:
            self.validation_finished.emit(False, self.api_key)


class ModScanner(QObject):
    """inputフォルダ内のModをスキャンし、翻訳対象の言語ファイルを抽出するワーカー。"""
    scan_finished = pyqtSignal(list)
    log_signal = pyqtSignal(str, str)

    def run(self):
        mod_infos =[]
        input_dir = Path(INPUT_DIR_NAME)
        lang_file_pattern = re.compile(r"assets/([^/]+)/lang/en_us\.json")

        for jar_path in sorted(input_dir.glob("*.jar")):
            try:
                with zipfile.ZipFile(jar_path, 'r') as zf:
                    # lang/en_us.json で終わるファイルのみを対象に絞り込み最適化
                    lang_files =[n for n in zf.namelist() if n.lower().endswith("en_us.json")]
                    for original_name in lang_files:
                        lower_name = original_name.lower().replace('\\', '/')
                        match = lang_file_pattern.search(lower_name)
                        if match:
                            mod_id = match.group(1)
                            mod_infos.append({"mod_id": mod_id, "filename": jar_path.name})
                            break
            except Exception as e:
                self.log_signal.emit("警告", f"{jar_path.name} のスキャン中にエラー: {e}")
        
        self.log_signal.emit("通知", f"スキャン完了: {len(mod_infos)}個のModが見つかりました。")
        self.scan_finished.emit(mod_infos)


class Worker(QObject):
    """翻訳処理のコアロジックを実行するバックグラウンドワーカー。"""
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    api_request_start_signal = pyqtSignal()
    api_request_end_signal = pyqtSignal()
    progress_reset_signal = pyqtSignal()

    PACK_META_FILE_NAME = "pack.mcmeta"
    ASSETS_PATH_TEMPLATE = "assets/{mod_id}/lang/{lang_code}.json"
    EN_US_LANG_CODE = "en_us"
    JA_JP_LANG_CODE = "ja_jp"
    EN_US_SEARCH_PATTERN = re.compile(r"assets/([^/]+)/lang/en_us\.json")
    TRANSLATION_CHUNK_SIZE = 250

    def __init__(self, api_key: str, pack_format: int, glossary: dict, system_prompt: str, target_mod_ids: list):
        super().__init__()
        self.api_key = api_key
        self.pack_format = pack_format
        self.glossary = glossary
        self.system_prompt_template = system_prompt
        self.target_mod_ids = target_mod_ids
        self.is_running = True
        self.input_dir = Path(INPUT_DIR_NAME)
        self.output_dir = Path(OUTPUT_DIR_NAME)
        self.deleted_entry_manager = DeletedEntryManager()

    def stop(self):
        self.is_running = False

    def run(self):
        self.progress_reset_signal.emit()
        
        if not self._check_prompt_template():
            self.finished_signal.emit()
            return

        if self.glossary:
            self.log_signal.emit("通知", f"設定ファイルから{len(self.glossary)}個の用語を読み込みました。")

        try:
            genai.configure(api_key=self.api_key)
            self.log_signal.emit("通知", "処理を開始します...")

            mod_infos = self._scan_input_mods()
            if not mod_infos:
                self.log_signal.emit("警告", "処理対象として選択されたModが見つかりませんでした。")
                self.finished_signal.emit()
                return

            self.log_signal.emit("通知", f"{len(mod_infos)}個のModを検出・対象としました。")
            total_added, processed_mods = 0, 0

            for mod_info in mod_infos:
                if not self.is_running:
                    self.log_signal.emit("警告", "処理が中断されました。")
                    break
                
                try:
                    added_count = self._process_mod(mod_info)
                    if added_count is not None:
                        total_added += added_count
                        processed_mods += 1
                except Exception as e:
                    self.log_signal.emit("失敗", f"[{mod_info['mod_id']}] 処理中に予期せぬエラーが発生しました: {e}")

            if self.is_running and processed_mods > 0:
                self._create_pack_mcmeta()
                self.deleted_entry_manager.save()
                self._check_unloaded_mods()
            
            msg = f"結果: {processed_mods}個のModを処理し、合計{total_added}個のキーを更新しました。"
            self.log_signal.emit("成功", msg)

        except Exception as e:
            if isinstance(e, (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated)):
                 self.error_signal.emit(f"APIキーが無効、または権限がありません。\n詳細: {e}")
            else:
                 self.error_signal.emit(f"致命的なエラーが発生しました: {e}")
        finally:
            self.finished_signal.emit()

    def _check_prompt_template(self) -> bool:
        if not self.system_prompt_template or "{json_to_translate}" not in self.system_prompt_template:
            self.error_signal.emit("設定の `system_prompt` にプレースホルダー `{json_to_translate}` が必要です。")
            return False
        return True

    def _scan_input_mods(self) -> list[dict]:
        mod_infos =[]
        for jar_path in sorted(self.input_dir.glob("*.jar")):
            if not self.is_running:
                break
            try:
                with zipfile.ZipFile(jar_path, 'r') as zf:
                    name_map = {n.lower().replace('\\', '/'): n for n in zf.namelist()}
                    for lower_name, original_name in name_map.items():
                        match = self.EN_US_SEARCH_PATTERN.search(lower_name)
                        if match:
                            mod_id = match.group(1)
                            if mod_id in self.target_mod_ids:
                                ja_jp_path_key = self.ASSETS_PATH_TEMPLATE.format(mod_id=mod_id, lang_code=self.JA_JP_LANG_CODE)
                                mod_infos.append({
                                    "mod_id": mod_id,
                                    "jar_path": jar_path,
                                    "en_us_path": original_name,
                                    "ja_jp_path_in_jar": name_map.get(ja_jp_path_key)
                                })
                                break
            except Exception as e:
                self.log_signal.emit("警告", f"[{jar_path.name}] のスキャン中にエラー: {e}")
        return mod_infos

    def _load_json_from_jar(self, jar_path: Path, path_in_jar: str) -> dict | None:
        if not path_in_jar: 
            return None
        try:
            with zipfile.ZipFile(jar_path, 'r') as zf:
                with zf.open(path_in_jar) as f:
                    content = f.read().decode('utf-8')
                    return json.loads(content)
        except Exception as e:
            self.log_signal.emit("警告", f"{jar_path.name}内の{path_in_jar}の読み込みに失敗しました: {e}")
            return None

    def _process_mod(self, mod_info: dict) -> int | None:
        mod_id = mod_info["mod_id"]
        jar_path = mod_info["jar_path"]
        
        english_data = self._load_json_from_jar(jar_path, mod_info["en_us_path"])
        if english_data is None:
            self.log_signal.emit("失敗", f"[{mod_id}] 必須の英語ファイルを読み込めませんでした。処理をスキップします。")
            return None

        output_lang_path = self.output_dir / self.ASSETS_PATH_TEMPLATE.format(mod_id=mod_id, lang_code=self.JA_JP_LANG_CODE)
        base_lang_data = load_json_file(output_lang_path)
        if base_lang_data:
            self.log_signal.emit("通知", f"[{mod_id}] {output_lang_path.name}から既存の翻訳を読み込みました。")
        
        jar_lang_data = self._load_json_from_jar(jar_path, mod_info["ja_jp_path_in_jar"])
        if jar_lang_data:
            self.log_signal.emit("通知", f"[{mod_id}] 公式訳を読み込み、不足分をマージします。")
            for k, v in jar_lang_data.items():
                if k not in base_lang_data and k in english_data:
                    base_lang_data[k] = v

        # 不要な古いキーの整理と退避
        keys_to_delete = set(base_lang_data.keys()) - set(english_data.keys())
        past_deleted_for_mod = self.deleted_entry_manager.entries.get(mod_id, {})
        keys_to_delete -= set(past_deleted_for_mod.keys())

        if keys_to_delete:
            mod_deleted = {key: base_lang_data.pop(key) for key in keys_to_delete}
            self.deleted_entry_manager.add_deleted_keys(mod_id, mod_deleted)
            self.log_signal.emit("通知", f"[{mod_id}] 不要になった古いキーを{len(keys_to_delete)}個削除しました。")

        # 翻訳対象の抽出
        items_to_translate = {k: v for k, v in english_data.items() if k not in base_lang_data}
        if not items_to_translate:
            self.log_signal.emit("成功", f"[{mod_id}] 翻訳は既に最新です。")
            save_json_file(output_lang_path, base_lang_data)
            return 0
        
        self.log_signal.emit("通知", f"[{mod_id}] {len(items_to_translate)}個の新しいキーを翻訳します。")
        
        translated_items, error = self._translate_in_chunks(items_to_translate, mod_id)
        if error:
            self.log_signal.emit("失敗", error)
            return None
        
        base_lang_data.update(translated_items)
        if save_json_file(output_lang_path, base_lang_data):
            added_count = len(translated_items)
            self.log_signal.emit("成功", f"[{mod_id}] 翻訳完了。{added_count}個のキーを追加しました。")
            return added_count
        else:
            self.log_signal.emit("失敗", f"[{mod_id}] {output_lang_path.name} の保存に失敗しました。")
            return None

    def _translate_in_chunks(self, items: dict, mod_id: str) -> tuple[dict, str | None]:
        all_translated = {}
        item_keys = list(items.keys())
        total_chunks = math.ceil(len(item_keys) / self.TRANSLATION_CHUNK_SIZE)
        
        if total_chunks > 1:
            self.log_signal.emit("通知", f"[{mod_id}] 翻訳対象が多いため、{total_chunks}個のバッチに分割します。")

        for i in range(total_chunks):
            if not self.is_running:
                return {}, "処理が中断されました。"
            
            chunk_keys = item_keys[i * self.TRANSLATION_CHUNK_SIZE:(i + 1) * self.TRANSLATION_CHUNK_SIZE]
            chunk_to_translate = {key: items[key] for key in chunk_keys}
            
            if total_chunks > 1:
                self.log_signal.emit("通知", f"[{mod_id}] バッチ {i + 1}/{total_chunks} を翻訳中...")
                
            translated_chunk, error_msg = self._translate_with_gemini(chunk_to_translate)
            if error_msg:
                return {}, f"[{mod_id}] 翻訳中にエラーが発生しました: {error_msg}"
            
            all_translated.update(translated_chunk)
            
        return all_translated, None

    def _translate_with_gemini(self, items: dict) -> tuple[dict | None, str | None]:
        if not items: return {}, None
        try:
            self.api_request_start_signal.emit()
            
            # APIがJSONモードをサポートしている場合の安全策を追加
            try:
                model = genai.GenerativeModel('gemini-3-flash-preview', generation_config={"response_mime_type": "application/json"})
            except TypeError:
                model = genai.GenerativeModel('gemini-3-flash-preview')

            json_string = json.dumps(items, indent=2, ensure_ascii=False)
            
            glossary_part = ""
            if self.glossary:
                glossary_json = json.dumps(self.glossary, indent=2, ensure_ascii=False)
                glossary_part = f"#用語集\n{glossary_json}\n--------------\n\n"

            final_prompt = glossary_part + self.system_prompt_template.format(json_to_translate=json_string)
            response = model.generate_content(final_prompt)
            
            # 堅牢性のため正規表現での抽出を維持
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not match:
                return None, f"APIの応答からJSONを抽出できませんでした。応答先頭: {response.text[:100]}..."
                
            translated_dict = json.loads(match.group(0))
            if set(translated_dict.keys()) != set(items.keys()):
                return None, "翻訳によってキーが変更または欠損しました。翻訳結果を破棄します。"
                
            return translated_dict, None
        except json.JSONDecodeError as e:
            return None, f"JSON解析エラーが発生しました: {e}"
        except Exception as e:
            return None, f"API通信エラーが発生しました: {e}"
        finally:
            self.api_request_end_signal.emit()

    def _create_pack_mcmeta(self):
        pack_meta_path = self.output_dir / self.PACK_META_FILE_NAME
        existing_meta = load_json_file(pack_meta_path)
        
        # 既存メタファイルがあり、かつバージョンが同じ場合は更新をスキップ
        if existing_meta and existing_meta.get("pack", {}).get("pack_format") == self.pack_format:
            return

        self.log_signal.emit("通知", f"\n{self.PACK_META_FILE_NAME} を生成/更新しています...")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        desc = f"Mod translation generated by ModL10n.\nLast updated: {now}"
        mcmeta = {
            "pack": {
                "pack_format": self.pack_format,
                "description": desc
            }
        }
        if save_json_file(pack_meta_path, mcmeta):
            self.log_signal.emit("成功", f"{self.PACK_META_FILE_NAME} を生成/更新しました。")
        else:
            self.log_signal.emit("失敗", f"{self.PACK_META_FILE_NAME} の生成に失敗しました。")

    def _check_unloaded_mods(self):
        assets_dir = self.output_dir / "assets"
        if assets_dir.exists():
            output_mods = [d.name for d in assets_dir.iterdir() if d.is_dir()]
            unloaded_mods =[m for m in output_mods if m not in self.target_mod_ids]
            if unloaded_mods:
                self.log_signal.emit("警告", f"読み込まれていないModのフォルダがoutput内に存在します。<br>{', '.join(unloaded_mods)}")


# --- UIコンポーネント ---
class ConsoleLineEdit(QLineEdit):
    """コマンド入力を受け付ける疑似コンソール用のカスタム入力欄。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("console_input")
        self.setPlaceholderText("コマンドを入力してください...")
        
        self.command_list =[
            "/reload",
            "/start",
            "/search value ",
            "/search key ",
            "/delete",
            "/extract",
            "/save",
            "/merge "
        ]
        
        self.completer_obj = QCompleter(self.command_list, self)
        self.completer_obj.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer_obj.setCompletionMode(QCompleter.PopupCompletion)
        
        list_view = QListView()
        list_view.setObjectName("completer_list")
        self.completer_obj.setPopup(list_view)
        self.setCompleter(self.completer_obj)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.text() or self.text() == "/":
            self.completer_obj.setCompletionPrefix("")
            self.completer_obj.complete()


class MainWindow(QWidget):
    """アプリケーションのメインウィンドウ。"""
    VERSION_FORMATS = {
        "1.21": 34, "1.20.5 - 1.20.6": 32, "1.20.3 - 1.20.4": 22,
        "1.20.2": 18, "1.20 - 1.20.1": 15, "1.19.4": 13, "1.19.3": 12,
        "1.19 - 1.19.2": 9, "1.18 - 1.18.2": 8, "1.17 - 1.17.1": 7,
        "1.16.2 - 1.16.5": 6, "1.15 - 1.15.2": 5,
    }
    LOG_COLORS = {"通知": "#c3c8d8", "成功": "#2ecc71", "警告": "#f39c12", "失敗": "#e74c3c"}

    def __init__(self):
        super().__init__()
        self.worker_thread = self.validator_thread = self.scanner_thread = None
        self.main_worker = self.api_validator = self.mod_scanner = None
        
        self.valid_api_key = None
        self.config_manager = ConfigManager(Path(CONFIG_FILE_NAME))
        self.config = self.config_manager.load_config()
        
        self.current_search_results = {}
        self.last_search_word = ""

        self.init_ui()
        self._apply_config_to_ui()
        self.scan_mods_and_update_list()

    def init_ui(self):
        self.setWindowTitle(f'ModL10n v{APP_VERSION}')
        self.setGeometry(150, 150, 1000, 700)
        self.setObjectName("main_widget")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        main_layout.addWidget(self._create_left_panel(), 1)
        main_layout.addWidget(self._create_right_panel(), 2)

    def _create_left_panel(self) -> QWidget:
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        
        header_text = f'MODL10N <span style="font-size: 12pt; color: #8a91a3; font-family: sans-serif; font-weight: bold;">v{APP_VERSION}</span>'
        header_title = QLabel(header_text)
        header_title.setObjectName("header_title")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(1, 2)
        shadow.setColor(QColor(0, 0, 0, 120))
        header_title.setGraphicsEffect(shadow)
        
        left_layout.addWidget(header_title)

        api_group = QGroupBox("1. 基本設定")
        api_layout = QVBoxLayout(api_group)
        
        self.version_combo = QComboBox()
        self.version_combo.addItems(self.VERSION_FORMATS.keys())
        self.version_combo.currentTextChanged.connect(self._on_version_changed)

        self.api_key_input = QLineEdit(placeholderText="Please enter API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.editingFinished.connect(self._start_api_key_validation)
        self.api_status_label = QLabel("")

        api_layout.addWidget(QLabel("Minecraft Version:"))
        api_layout.addWidget(self.version_combo)
        api_layout.addWidget(QLabel("Gemini API Key:"))
        api_layout.addWidget(self.api_key_input)
        api_layout.addWidget(self.api_status_label)
        
        left_layout.addWidget(api_group)

        mods_group = QGroupBox("2. 翻訳対象の確認")
        mods_layout = QVBoxLayout(mods_group)
        
        check_buttons_layout = QHBoxLayout()
        self.check_all_btn = QPushButton("✓ 一括選択")
        self.check_all_btn.setObjectName("small_btn")
        self.check_all_btn.clicked.connect(self._check_all_mods)
        
        self.uncheck_all_btn = QPushButton("☐ 一括解除")
        self.uncheck_all_btn.setObjectName("small_btn")
        self.uncheck_all_btn.clicked.connect(self._uncheck_all_mods)
        
        check_buttons_layout.addWidget(self.check_all_btn)
        check_buttons_layout.addWidget(self.uncheck_all_btn)
        check_buttons_layout.addStretch()
        mods_layout.addLayout(check_buttons_layout)

        self.mod_list_widget = QListWidget()
        self.mod_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mod_list_widget.setTextElideMode(Qt.ElideRight)
        mods_layout.addWidget(self.mod_list_widget)
        
        folder_buttons_layout = QHBoxLayout()
        scan_button = QPushButton("スキャン更新")
        open_input_button = QPushButton(f"{INPUT_DIR_NAME}を開く")
        open_output_button = QPushButton(f"{OUTPUT_DIR_NAME}を開く")
        
        scan_button.clicked.connect(self._on_scan_button_clicked)
        open_input_button.clicked.connect(lambda: self._open_directory_in_explorer(Path(INPUT_DIR_NAME)))
        open_output_button.clicked.connect(lambda: self._open_directory_in_explorer(Path(OUTPUT_DIR_NAME)))
        
        folder_buttons_layout.addWidget(open_input_button)
        folder_buttons_layout.addWidget(open_output_button)
        mods_layout.addLayout(folder_buttons_layout)
        mods_layout.addWidget(scan_button)
        
        left_layout.addWidget(mods_group, 1)

        self.run_btn = QPushButton("翻訳実行")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._on_run_button_clicked)
        left_layout.addWidget(self.run_btn)
        
        return left_widget

    def _create_right_panel(self) -> QWidget:
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_widget.setStyleSheet("background-color: #282c34; border-radius: 8px;")
        
        self.log_area = QTextEdit()
        self.log_area.setObjectName("log_area")
        self.log_area.setReadOnly(True)
        right_layout.addWidget(self.log_area)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_fake_progress)
        self.current_progress = 0

        self.console_input = ConsoleLineEdit()
        self.console_input.returnPressed.connect(self._handle_console_command)
        right_layout.addWidget(self.console_input)

        return right_widget

    # --- UIイベントハンドラ ---
    def _log_command(self, cmd_text: str):
        formatted_input = f'<font color="#2b79eb"><b>&gt; {cmd_text.replace(" ", "&nbsp;")}</b></font>'
        self.log_area.append(formatted_input)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def _on_scan_button_clicked(self):
        self._log_command("/reload")
        self.scan_mods_and_update_list()

    def _on_run_button_clicked(self):
        self._log_command("/start")
        self.start_processing()

    def _check_all_mods(self):
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            if item.data(Qt.UserRole):
                item.setCheckState(Qt.Checked)

    def _uncheck_all_mods(self):
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            if item.data(Qt.UserRole):
                item.setCheckState(Qt.Unchecked)

    # --- コンソールコマンド処理 ---
    def _handle_console_command(self):
        cmd_text = self.console_input.text().strip()
        if not cmd_text:
            return
            
        self.console_input.clear()
        self._log_command(cmd_text)
        
        parts = cmd_text.split(maxsplit=2)
        cmd = parts[0].lower()
        
        if cmd == "/reload":
            self.scan_mods_and_update_list()
        elif cmd == "/start":
            self.start_processing()
        elif cmd == "/search":
            if len(parts) >= 3:
                mode = parts[1].lower()
                word = parts[2]
                if mode in ["value", "key"]:
                    self._execute_search(mode, word)
                else:
                    self.log_message("警告", "検索モードは 'value' または 'key' を指定してください。")
            else:
                self.log_message("警告", "コマンド形式が不正です。使用法: /search [value/key][ワード]")
        elif cmd in["/delete", "/extract", "/save"]:
            if not self.current_search_results:
                self.log_message("警告", "検索結果が存在しません。先に /search でエントリを見つけてください。")
            else:
                if cmd == "/delete":
                    self._execute_delete()
                elif cmd == "/save":
                    self._execute_save(prefix="saved_entries")
                elif cmd == "/extract":
                    self._execute_extract()
        elif cmd == "/merge":
            if len(parts) >= 2:
                # maxsplit=2 で分割されているため、ファイル名にスペースが含まれるケースを考慮して結合
                filename = " ".join(parts[1:])
                self._execute_merge(filename)
            else:
                self.log_message("警告", "ファイル名が指定されていません。使用法: /merge[ファイル名]")
        else:
            self.log_message("警告", f"不明なコマンドです: {cmd}")
            self.log_message("通知", "使用可能: /reload, /start, /search, /delete, /extract, /save, /merge")

    def _execute_search(self, mode: str, word: str):
        self.current_search_results.clear()
        self.last_search_word = word
        output_dir = Path(OUTPUT_DIR_NAME)
        
        if not output_dir.exists():
            self.log_message("警告", f"{OUTPUT_DIR_NAME} フォルダが存在しません。")
            return
            
        found_count = 0
        
        # 効率化のため対象を assets 配下の json のみに限定
        for json_file in output_dir.rglob("assets/**/*.json"):
            data = load_json_file(json_file)
            if not data:
                continue
                
            matches = {}
            for k, v in data.items():
                if not isinstance(v, str):
                    continue
                if (mode == "value" and word in v) or (mode == "key" and word in k):
                    matches[k] = v
                    
            if matches:
                self.current_search_results[json_file] = matches
                found_count += len(matches)
                
        if found_count > 0:
            self.log_message("成功", f"検索完了: {found_count} 件のエントリが見つかりました。")
            
            mod_ids = set()
            for f in self.current_search_results.keys():
                try:
                    parts = f.relative_to(output_dir).parts
                    if parts[0] == "assets" and len(parts) > 1:
                        mod_ids.add(parts[1])
                except ValueError:
                    pass
            
            mod_list_str = ", ".join(sorted(mod_ids))
            max_length = 80
            if len(mod_list_str) > max_length:
                mod_list_str = mod_list_str[:max_length] + "..."
                
            self.log_message("通知", f"対象Mod: {mod_list_str}")
        else:
            self.log_message("通知", "指定されたワードを含むエントリは見つかりませんでした。")

    def _execute_delete(self):
        deleted_total = 0
        for file_path, entries in self.current_search_results.items():
            data = load_json_file(file_path)
            if not data:
                continue
                
            original_len = len(data)
            for key in entries.keys():
                data.pop(key, None)
                
            deleted_count = original_len - len(data)
            if deleted_count > 0:
                if save_json_file(file_path, data):
                    deleted_total += deleted_count
                else:
                    self.log_message("失敗", f"{file_path.name} の保存に失敗しました。")
                    
        self.log_message("成功", f"削除完了: {deleted_total} 件のエントリをファイルから削除しました。")
        self.current_search_results.clear()

    def _execute_save(self, prefix: str = "saved_entries") -> bool:
        saved_total = 0
        extracted_data = {}
        for entries in self.current_search_results.values():
            extracted_data.update(entries)
            saved_total += len(entries)
            
        safe_word = re.sub(r'[\\/*?:"<>|]', "_", self.last_search_word) or "unknown"
        base_name = f"{prefix}_{safe_word}"
        save_path = Path(f"{base_name}.json")
        
        counter = 1
        while save_path.exists():
            save_path = Path(f"{base_name}_{counter}.json")
            counter += 1
        
        if save_json_file(save_path, extracted_data):
            self.log_message("成功", f"保存完了: {saved_total} 件のエントリを {save_path.name} に保存しました。")
            return True
        else:
            self.log_message("失敗", "ファイルの保存に失敗しました。")
            return False

    def _execute_extract(self):
        if self._execute_save(prefix="extracted_entries"):
            self._execute_delete()

    def _execute_merge(self, filename: str):
        merge_file_path = Path(filename)
        if not merge_file_path.exists():
            self.log_message("警告", f"指定されたファイルが見つかりません: {filename}")
            return
            
        merge_data = load_json_file(merge_file_path)
        if not merge_data:
            self.log_message("警告", f"{filename} から有効なJSONデータを読み込めませんでした。")
            return
            
        output_dir = Path(OUTPUT_DIR_NAME)
        if not output_dir.exists():
            self.log_message("警告", f"{OUTPUT_DIR_NAME} フォルダが存在しません。")
            return

        merged_total = 0
        updated_files = 0

        # outputディレクトリ内の対象jsonを走査
        for json_file in output_dir.rglob("assets/**/*.json"):
            data = load_json_file(json_file)
            if not data:
                continue
                
            updated = False
            for key, value in merge_data.items():
                if key in data:
                    data[key] = value
                    updated = True
                    merged_total += 1
                    
            if updated:
                if save_json_file(json_file, data):
                    updated_files += 1
                else:
                    self.log_message("失敗", f"{json_file.name} の保存に失敗しました。")
                    
        if merged_total > 0:
            self.log_message("成功", f"マージ完了: {updated_files} 個のファイルで合計 {merged_total} 件のエントリを上書きしました。")
        else:
            self.log_message("通知", "マージ対象のキーを持つエントリが output 内に見つかりませんでした。")

    # --- アニメーション関連 ---
    def _on_api_request_start(self):
        self.current_progress = 0
        self.progress_bar.setValue(0)
        self.anim_timer.start(50)

    def _on_api_request_end(self):
        self.anim_timer.stop()
        self.current_progress = 1000
        self.progress_bar.setValue(self.current_progress)

    def _on_progress_reset(self):
        self.anim_timer.stop()
        self.current_progress = 0
        self.progress_bar.setValue(0)

    def _update_fake_progress(self):
        remaining = 1000 - self.current_progress
        step = max(1, int(remaining * 0.08))
        self.current_progress += step
        if self.current_progress > 990:
            self.current_progress = 990
        self.progress_bar.setValue(self.current_progress)

    # --- アプリケーション状態管理 ---
    def _apply_config_to_ui(self):
        env_data = load_env()
        api_key = env_data.get("GEMINI_API_KEY", "")
        if api_key:
            self.api_key_input.setText(api_key)
            self._start_api_key_validation()
        
        version = self.config.get("minecraft_version")
        if version in self.VERSION_FORMATS:
            self.version_combo.setCurrentText(version)

    def _start_api_key_validation(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self._update_api_status('cleared')
            return
            
        self._update_api_status('checking')
        self.run_btn.setEnabled(False)
        
        if self.validator_thread and self.validator_thread.isRunning():
            self.validator_thread.quit()
            self.validator_thread.wait(1000)
            
        self.validator_thread = QThread()
        self.api_validator = ApiKeyValidator(api_key)
        self.api_validator.moveToThread(self.validator_thread)
        self.api_validator.validation_finished.connect(self._on_api_key_validation_finished)
        self.validator_thread.started.connect(self.api_validator.run)
        self.validator_thread.start()

    def _on_api_key_validation_finished(self, is_valid: bool, api_key: str):
        if api_key == self.api_key_input.text().strip():
            if is_valid:
                self.valid_api_key = api_key
                save_env("GEMINI_API_KEY", api_key)
                self._update_api_status('valid')
                self.run_btn.setEnabled(True)
            else:
                self.valid_api_key = None
                self._update_api_status('invalid')
                self.run_btn.setEnabled(False)
        
        if self.validator_thread:
            self.validator_thread.quit()
            self.validator_thread.wait(1000)

    def _on_version_changed(self, version_text: str):
        self.config["minecraft_version"] = version_text
        self.config_manager.save_config(self.config)

    def _update_api_status(self, status: str):
        if status == 'valid':
            self.api_status_label.setText("✔ Verified")
            self.api_status_label.setObjectName("api_status_valid")
        elif status == 'invalid':
            self.api_status_label.setText("✖ Invalid")
            self.api_status_label.setObjectName("api_status_invalid")
        elif status == 'checking':
            self.api_status_label.setText("... Verifying")
            self.api_status_label.setObjectName("api_status_checking")
        else:
            self.api_status_label.setText("")
            self.api_status_label.setObjectName("")
        self.api_status_label.style().unpolish(self.api_status_label)
        self.api_status_label.style().polish(self.api_status_label)

    def scan_mods_and_update_list(self):
        if self.scanner_thread and self.scanner_thread.isRunning():
            return
            
        self.scanner_thread = QThread()
        self.mod_scanner = ModScanner()
        self.mod_scanner.moveToThread(self.scanner_thread)
        self.mod_scanner.scan_finished.connect(self._update_mod_list)
        self.mod_scanner.log_signal.connect(self.log_message)
        self.scanner_thread.started.connect(self.mod_scanner.run)
        self.scanner_thread.start()

    def _update_mod_list(self, mod_infos: list):
        self.mod_list_widget.clear()
        if not mod_infos:
            self.mod_list_widget.addItem("対象のModが見つかりませんでした。")
        else:
            for mod in mod_infos:
                display_text = f"{mod['filename']}  ({mod['mod_id']})"
                item = QListWidgetItem(display_text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, mod['mod_id'])
                item.setToolTip(display_text)
                self.mod_list_widget.addItem(item)
                
        if self.scanner_thread:
            self.scanner_thread.quit()
            self.scanner_thread.wait(1000)

    def _open_directory_in_explorer(self, path: Path):
        absolute_path = path.resolve()
        try:
            if sys.platform == "win32":
                os.startfile(absolute_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", absolute_path])
            else:
                subprocess.run(["xdg-open", absolute_path])
        except Exception as e:
            self.show_error_message(f"フォルダを開けませんでした: {e}")

    def start_processing(self):
        if not self.valid_api_key:
            self.log_message("警告", "有効なAPIキーが設定されていません。")
            return

        target_mod_ids =[]
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            mod_id = item.data(Qt.UserRole)
            if mod_id and item.checkState() == Qt.Checked:
                target_mod_ids.append(mod_id)

        if not target_mod_ids:
            self.log_message("警告", "翻訳対象のModが1つも選択されていません。")
            return

        self.config = self.config_manager.load_config()
        pack_format = self.VERSION_FORMATS.get(self.config["minecraft_version"], 34)
        
        self.set_ui_enabled(False)
        self.log_area.clear()
        
        self.worker_thread = QThread()
        self.main_worker = Worker(
            self.valid_api_key, 
            pack_format, 
            self.config.get("glossary", {}),
            self.config.get("system_prompt", ""),
            target_mod_ids
        )
        self.main_worker.moveToThread(self.worker_thread)
        
        self.main_worker.log_signal.connect(self.log_message)
        self.main_worker.error_signal.connect(self.show_error_message)
        self.main_worker.finished_signal.connect(self.on_finished)
        self.main_worker.api_request_start_signal.connect(self._on_api_request_start)
        self.main_worker.api_request_end_signal.connect(self._on_api_request_end)
        self.main_worker.progress_reset_signal.connect(self._on_progress_reset)
        
        self.worker_thread.started.connect(self.main_worker.run)
        self.worker_thread.start()

    def log_message(self, level: str, message: str):
        color = self.LOG_COLORS.get(level.upper(), "#d1d1d1")
        formatted_message = f'<font color="{color}"><b>[{level.upper()}]</b>&nbsp;{message.replace(" ", "&nbsp;")}</font>'
        self.log_area.append(formatted_message)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def show_error_message(self, message: str):
        self.log_message("失敗", f"FATAL: {message}")
        self.on_finished()

    def on_finished(self):
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(2000)
            
        self.set_ui_enabled(True)
        if not self.log_area.toPlainText().strip().endswith("操作が可能です。"):
            self.log_message("通知", "\n操作が可能です。")

    def set_ui_enabled(self, enabled: bool):
        self.api_key_input.setEnabled(enabled)
        self.version_combo.setEnabled(enabled)
        self.console_input.setEnabled(enabled)
        
        if enabled:
            if self.valid_api_key:
                self.run_btn.setEnabled(True)
            self.run_btn.setText("翻訳実行")
        else:
            self.run_btn.setEnabled(False)
            self.run_btn.setText("処理中...")

    def closeEvent(self, event):
        if self.main_worker:
            self.main_worker.stop()

        for thread in[self.worker_thread, self.validator_thread, self.scanner_thread]:
            if thread and thread.isRunning():
                thread.quit()
                thread.wait(2000)
        event.accept()

def main():
    try:
        Path(INPUT_DIR_NAME).mkdir(exist_ok=True)
        Path(OUTPUT_DIR_NAME).mkdir(exist_ok=True)
    except OSError as e:
        print(f"ディレクトリ作成エラー: {e}", file=sys.stderr)
        sys.exit(1)
        
    app = QApplication(sys.argv)
    app.setStyleSheet(FINAL_STYLE)
    
    font = QFont()
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)
    
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()