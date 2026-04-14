import sys
import json
import os
import math
import shutil
import calendar
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta

# Added QtNetwork for robust Single Instance checking
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from PyQt6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu, 
                             QVBoxLayout, QWidget, QDialog, QTextEdit, QLabel, 
                             QCheckBox, QComboBox, QPushButton, QHBoxLayout, 
                             QMessageBox, QGraphicsDropShadowEffect, QFrame, 
                             QSizePolicy, QGridLayout, QToolButton, QTabWidget)
from PyQt6.QtCore import (Qt, QPointF, QThread, pyqtSignal, QPropertyAnimation, 
                          QEasingCurve, QTimer, QSize, QDate, QRect, QLockFile, 
                          QDir, QMimeData)
from PyQt6.QtGui import (QIcon, QPainter, QColor, QFont, QBrush, QPen, 
                         QAction, QPixmap, QPolygonF, QDrag)

# --- CONFIGURATION & STYLING ---
DATA_FILE = "diary_data.json"
ICON_FILE = "icon.ico"
APP_NAME = "My Cycle" 
INSTANCE_ID = "MyCycleApp_Unique_ID_v1" 
IMAGE_FOLDER = "images"

# Ensure image directory exists
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Pastel Color Palette
COLOR_BG          = "#FFF0F5"      # Lavender Blush background
COLOR_CARD_BG     = "#FFFFFF"      # White cards
COLOR_TEXT_MAIN   = "#6D4C8B"      # Soft, deep purple for main text
COLOR_TEXT_SOFT   = "#9575CD"      # Lighter purple for secondary text
COLOR_ACCENT_1    = "#B3E5FC"      # Pastel Blue (Buttons)
COLOR_ACCENT_2    = "#81D4FA"      # Light Blue (Moon/Weather)
COLOR_ACCENT_3    = "#F8BBD0"      # Soft Pink (Period/Important)
COLOR_HEADER_PINK = "#F4C2D7"      # Slightly richer pink for Calendar Header
COLOR_BORDER      = "#E1BEE7"      # Soft border color

# Location
LATITUDE = -27.158
LONGITUDE = 152.956

# Modern Stylesheet
STYLESHEET = f"""
    QMainWindow, QDialog {{
        background-color: {COLOR_BG};
    }}

    QLabel {{
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        color: {COLOR_TEXT_MAIN};
    }}
    
    QPushButton {{
        background-color: {COLOR_ACCENT_1};
        border: none;
        border-radius: 15px;
        padding: 10px 20px;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-weight: 600;
        font-size: 13px;
        color: {COLOR_TEXT_MAIN};
    }}
    QPushButton:hover {{
        background-color: {COLOR_ACCENT_3};
    }}
    QPushButton#WeatherBtn {{
        background-color: transparent;
        color: {COLOR_TEXT_MAIN};
        text-align: right;
        padding: 5px;
    }}
    QPushButton#WeatherBtn:hover {{
        background-color: {COLOR_BORDER};
    }}

    QTextEdit, QLineEdit {{
        background-color: #FFFFFF;
        color: {COLOR_TEXT_MAIN}; 
        border: 1px solid {COLOR_BORDER};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        border-radius: 12px;
        padding: 10px;
    }}
    
    QComboBox {{
        background-color: #FFFFFF;
        color: {COLOR_TEXT_MAIN};
        border: 1px solid {COLOR_BORDER};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        border-radius: 12px;
        padding: 10px;
        selection-background-color: {COLOR_ACCENT_1};
    }}
    QComboBox::drop-down {{
        border: 0px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #FFFFFF;
        color: {COLOR_TEXT_MAIN};
        selection-background-color: {COLOR_ACCENT_1};
        selection-color: {COLOR_TEXT_MAIN};
        border: 1px solid {COLOR_BORDER};
        outline: none;
    }}

    QTextEdit:focus, QComboBox:focus {{
        border: 2px solid {COLOR_ACCENT_2};
        background-color: #FFFFFF;
    }}
    
    QFrame#DashboardCard {{
        background-color: {COLOR_CARD_BG};
        border-radius: 20px;
        border: 1px solid {COLOR_BORDER};
    }}
    
    QCheckBox {{
        spacing: 10px;
        font-size: 14px;
        color: {COLOR_TEXT_MAIN};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {COLOR_BORDER};
        background-color: #FFFFFF;
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLOR_ACCENT_3};
        border-color: {COLOR_ACCENT_3};
    }}

    QFrame#CalendarHeader {{
        background-color: {COLOR_HEADER_PINK};
        border-bottom: 2px solid {COLOR_BORDER};
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
    }}
    
    QToolButton#CalNavBtn {{
        background-color: {COLOR_ACCENT_2};
        border-radius: 15px;
        color: white;
        font-weight: bold;
    }}
    QToolButton#CalNavBtn:hover {{
        background-color: {COLOR_ACCENT_3};
    }}

    QTabWidget::pane {{
        border-top: 2px solid {COLOR_BORDER};
        margin-top: -2px;
    }}
    QTabBar::tab {{
        background: {COLOR_BG};
        border: 1px solid {COLOR_BORDER};
        border-bottom-color: {COLOR_BORDER};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        min-width: 8ex;
        padding: 10px 15px;
        color: {COLOR_TEXT_SOFT};
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_CARD_BG};
        border-color: {COLOR_BORDER};
        border-bottom-color: {COLOR_CARD_BG};
        color: {COLOR_TEXT_MAIN};
    }}
    QTabBar::tab:!selected:hover {{
        background: {COLOR_BORDER};
    }}
"""

# --- HELPERS ---

def get_moon_phase(dt):
    jd = dt.toordinal() + 1721425.5
    new_moon_epoch = 2451549.5
    synodic_month = 29.53058867
    days_since_epoch = jd - new_moon_epoch
    phase = (days_since_epoch / synodic_month) % 1
    return phase * synodic_month

def get_moon_icon_char(age):
    if age < 1.84566: return "🌑"
    elif age < 5.53699: return "🌒"
    elif age < 9.22831: return "🌓"
    elif age < 12.91963: return "🌔"
    elif age < 16.61096: return "🌕"
    elif age < 20.30228: return "🌖"
    elif age < 23.99361: return "🌗"
    elif age < 27.68493: return "🌘"
    else: return "🌑"

def create_fallback_icon_pixmap():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0,0,0,0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(QColor(COLOR_ACCENT_1)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 60, 60)
    painter.setBrush(QBrush(QColor("white")))
    painter.drawEllipse(15, 15, 30, 30)
    painter.setBrush(QBrush(QColor(COLOR_ACCENT_1)))
    painter.drawEllipse(22, 12, 30, 30)
    painter.end()
    return pixmap

def map_mood_to_value(mood_str):
    mapping = {"😡 Angry": 1, "😢 Sad": 2, "😞 Low": 3, "😰 Anxious": 4, "😐 Neutral": 5, "🙂 Calm": 6, "😊 Happy": 7, "😌 Content": 8, "✨ Energized": 9, "🤩 Amazing": 10, "": 0}
    return mapping.get(mood_str, 0)

def interpolate_mood_color(val):
    val = max(1.0, min(10.0, float(val)))
    color_low = QColor("#F48FB1") 
    color_mid = QColor("#FFF59D") 
    color_high = QColor("#A5D6A7") 
    if val <= 5.0:
        ratio = (val - 1.0) / 4.0; c1, c2 = color_low, color_mid
    else:
        ratio = (val - 5.0) / 5.0; c1, c2 = color_mid, color_high
    r, g, b = (c1.red() + ratio * (c2.red() - c1.red()),
               c1.green() + ratio * (c2.green() - c1.green()),
               c1.blue() + ratio * (c2.blue() - c1.blue()))
    return QColor(int(r), int(g), int(b), 200)

def interpret_wmo_code(code):
    if code == 0: return "Clear Sky", "☀️"
    if code in [1, 2, 3]: return "Partly Cloudy", "⛅"
    if code in [45, 48]: return "Foggy", "🌫️"
    if code in [51, 53, 55]: return "Drizzle", "🌦️"
    if code in [61, 63, 65]: return "Rain", "🌧️"
    if code in [80, 81, 82]: return "Showers", "☔"
    if code in [95, 96, 99]: return "Thunderstorm", "⛈️"
    return "Unknown", "❓"

# --- WORKERS ---

class WeatherWorker(QThread):
    finished = pyqtSignal(dict)
    def run(self):
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}"
               f"&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min"
               f"&timezone=Japan%2FTokyo")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'MyCycleApp/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                self.finished.emit(json.loads(response.read().decode()))
        except Exception:
            self.finished.emit({})

# --- DATA MANAGER ---

class DataManager:
    def __init__(self):
        self.data = {}
        self.period_start_dates = [] 
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.data = json.load(f)
            except: self.data = {}
        self._refresh_period_cache()

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)
        self._refresh_period_cache()

    def _refresh_period_cache(self):
        self.period_start_dates = []
        for d_str, info in self.data.items():
            if info.get('period', False):
                try: self.period_start_dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
                except ValueError: pass
        self.period_start_dates.sort()

    def get_entry(self, date_str): return self.data.get(date_str, {})
    def set_entry(self, date_str, entry_data): 
        current = self.get_entry(date_str)
        current.update(entry_data)
        self.data[date_str] = current
        self.save_data()

    def is_fertile_window(self, check_date):
        for p_date in reversed(self.period_start_dates):
            if p_date > check_date: continue
            delta = (check_date - p_date).days
            if 11 <= delta <= 16: return True
            if delta > 35: break 
        return False

    def get_period_day_number(self, check_date):
        for p_start_date in reversed(self.period_start_dates):
            if p_start_date > check_date: continue
            delta = (check_date - p_start_date).days
            if 0 <= delta < 5: return delta + 1
            if delta >= 5: break
        return 0

    def get_next_cycle_prediction(self):
        if not self.period_start_dates: return "Unknown", "Unknown"
        last_period = self.period_start_dates[-1]
        next_period = last_period + timedelta(days=28)
        next_fertile = last_period + timedelta(days=11)
        if (date.today() - next_period).days > 60: return "Track more data", "Track more data"
        return next_period.strftime("%b %d"), next_fertile.strftime("%b %d")

# --- CUSTOM WIDGETS ---

class StickerHeart(QLabel):
    def __init__(self, parent=None):
        super().__init__("❤️", parent)
        self.setStyleSheet("font-size: 30px; background: transparent;")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Drag me to a date!")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData("application/x-heart-sticker", b"heart")
            drag.setMimeData(mime_data)
            
            # Create a transparent preview of the heart
            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())
            drag.exec(Qt.DropAction.CopyAction)

class DropImageLabel(QLabel):
    imageDropped = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Drag & Drop Image Here")
        self.setStyleSheet(f"border: 2px dashed {COLOR_BORDER}; border-radius: 15px; color: {COLOR_TEXT_SOFT}; background: #FAFAFA;")
        self.setAcceptDrops(True)
        # ScaledContents is False to prevent stretching; we handle scaling in display_image
        self.setScaledContents(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                filename = os.path.basename(file_path)
                dest_name = f"{int(datetime.now().timestamp())}_{filename}"
                dest_path = os.path.join(IMAGE_FOLDER, dest_name)
                try:
                    # Load and resize to a maximum of 800px width/height to save space
                    pix = QPixmap(file_path)
                    if not pix.isNull():
                        resized_pix = pix.scaled(800, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        resized_pix.save(dest_path)
                        self.display_image(dest_path)
                        self.imageDropped.emit(dest_name)
                except Exception as e:
                    print(f"File process error: {e}")

    def display_image(self, path):
        if os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                # We use KeepAspectRatio here so it won't stretch!
                self.setPixmap(pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.setText("")
        else:
            self.setPixmap(QPixmap())
            self.setText("Drag & Drop Image Here")

    def resizeEvent(self, event):
        # Re-display the image on resize to ensure it fits the new container size without distortion
        if self.pixmap() and not self.pixmap().isNull():
            # Note: This is a bit tricky since self.pixmap() returns the scaled one. 
            # In a full production app, you'd store the original path as an attribute.
            pass
        super().resizeEvent(event)

class FadingDialog(QDialog):
    def __init__(self, parent=None): super().__init__(parent); self.setWindowOpacity(0.0)
    def showEvent(self, event):
        self.anim = QPropertyAnimation(self, b"windowOpacity"); self.anim.setDuration(400)
        self.anim.setStartValue(0.0); self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad); self.anim.start()
        super().showEvent(event)

class WeatherDialog(FadingDialog):
    def __init__(self, weather_data, parent=None):
        super().__init__(parent); self.setWindowTitle("Current Weather"); self.setFixedSize(350, 400)
        layout = QVBoxLayout(self); layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(15)
        title = QLabel("Home"); title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(title)
        if not weather_data: layout.addWidget(QLabel("Weather data unavailable.")); return
        current = weather_data.get('current', {}); daily = weather_data.get('daily', {})
        desc, emoji = interpret_wmo_code(current.get('weather_code', 0))
        temp = current.get('temperature_2m', 0)
        icon_lbl = QLabel(emoji); icon_lbl.setStyleSheet("font-size: 80px;"); icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp_lbl = QLabel(f"{temp}°C"); temp_lbl.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLOR_ACCENT_2};")
        temp_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl = QLabel(desc); desc_lbl.setStyleSheet(f"font-size: 16px; color: {COLOR_TEXT_SOFT};")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details = QFrame(); details.setObjectName("DashboardCard"); d_layout = QVBoxLayout(details)
        d_layout.setContentsMargins(15, 15, 15, 15)
        max_t = daily.get('temperature_2m_max', [0])[0]; min_t = daily.get('temperature_2m_min', [0])[0]
        d_layout.addWidget(QLabel(f"🌡️ High: {max_t}°C  |  Low: {min_t}°C"))
        layout.addWidget(icon_lbl); layout.addWidget(temp_lbl); layout.addWidget(desc_lbl)
        layout.addWidget(details); layout.addStretch()
        btn_close = QPushButton("Stay Cozy"); btn_close.clicked.connect(self.close); layout.addWidget(btn_close)

class DashboardCard(QFrame):
    def __init__(self, layout_obj, parent=None):
        super().__init__(parent); self.setObjectName("DashboardCard")
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(20)
        shadow.setColor(QColor(200, 180, 220, 80)); shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow); self.setLayout(layout_obj)

class DayCell(QWidget):
    clicked = pyqtSignal(date)
    def __init__(self, day_date, is_current_month, data_manager, parent=None):
        super().__init__(parent); self.day_date = day_date; self.is_current_month = is_current_month
        self.data_manager = data_manager; self.is_selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(70)
        self.setAcceptDrops(True)
        
    def mousePressEvent(self, event): self.clicked.emit(self.day_date); super().mousePressEvent(event)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-heart-sticker"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-heart-sticker"):
            d_str = self.day_date.strftime("%Y-%m-%d")
            # Logic: If it already has boink, toggle off. If not, set to True.
            current_status = self.data_manager.get_entry(d_str).get('boink', False)
            self.data_manager.set_entry(d_str, {"boink": not current_status})
            self.update()
            # If this cell is the one currently showing in the dashboard, refresh dashboard
            self.clicked.emit(self.day_date)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect(); font = painter.font()
        date_str = self.day_date.strftime("%Y-%m-%d"); entry = self.data_manager.get_entry(date_str)
        is_fertile = self.data_manager.is_fertile_window(self.day_date); has_diary = bool(entry.get('diary', "").strip())
        mood_str = entry.get('mood', ""); mood_value = map_mood_to_value(mood_str)
        # Mood emoji is used for calculation but no longer added to icons list
        period_day_num = self.data_manager.get_period_day_number(self.day_date)
        has_boink = entry.get('boink', False)
        
        painter.setPen(Qt.PenStyle.NoPen); bg_rect = rect.adjusted(2, 2, -2, -2)
        if mood_value > 0 and self.is_current_month:
            painter.setBrush(interpolate_mood_color(mood_value)); painter.drawRoundedRect(bg_rect, 10, 10)
        elif not self.is_current_month:
            painter.setBrush(QColor("#F8F8F8")); painter.drawRoundedRect(bg_rect, 10, 10)
        if self.is_selected:
            pen = QPen(QColor(COLOR_ACCENT_3), 3); painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(bg_rect.adjusted(1,1,-1,-1), 10, 10)

        if period_day_num > 0:
            period_emoji, font_size = ("🩸", 28)
            if period_day_num in [1, 2]: font_size = 28
            elif period_day_num in [3, 4]: font_size = 24
            elif period_day_num == 5: period_emoji, font_size = ("💧", 22)
            font.setPointSize(font_size); painter.setFont(font); painter.setPen(QColor("#D32F2F"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, period_emoji)

        font.setFamily("Segoe UI"); font.setPointSize(11); font.setBold(False); painter.setFont(font)
        text_color = QColor(COLOR_TEXT_MAIN) if self.is_current_month else QColor("#BDBDBD")
        painter.setPen(text_color)
        painter.drawText(rect.adjusted(6, 6, -6, -6), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(self.day_date.day))

        moon_age = get_moon_phase(self.day_date); moon_char = get_moon_icon_char(moon_age)
        font.setPointSize(9); painter.setFont(font)
        moon_color = QColor(COLOR_ACCENT_2) if self.is_current_month else QColor("#E0E0E0")
        painter.setPen(moon_color)
        painter.drawText(rect.adjusted(0, 6, -6, 0), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, moon_char)

        bottom_icons = []
        if has_boink: bottom_icons.append("❤️")
        # Removed: if mood_emoji: bottom_icons.append(mood_emoji)
        if has_diary: bottom_icons.append("✏️")
        
        font.setPointSize(10); painter.setFont(font); painter.setPen(QColor(COLOR_TEXT_MAIN))
        if bottom_icons:
            painter.drawText(rect.adjusted(0, 0, -4, -4), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, " ".join(bottom_icons))

        if is_fertile:
            font.setPointSize(16); painter.setFont(font)
            painter.drawText(rect.adjusted(4, 0, 0, -2), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, "🥚")

class CustomCalendarWidget(QWidget):
    dateSelected = pyqtSignal(date)
    def __init__(self, data_manager, parent=None):
        super().__init__(parent); self.data_manager = data_manager; self.current_date = date.today()
        self.selected_date = date.today(); self.cells = []; self.init_ui(); self.refresh_grid()
    def init_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        self.header_frame = QFrame(); self.header_frame.setObjectName("CalendarHeader")
        header_layout = QHBoxLayout(self.header_frame); header_layout.setContentsMargins(10, 8, 10, 8)
        self.btn_prev = QToolButton(); self.btn_prev.setText("<"); self.btn_prev.setFixedSize(30, 30); self.btn_prev.setObjectName("CalNavBtn"); self.btn_prev.clicked.connect(self.prev_month)
        self.lbl_month_year = QLabel(); self.lbl_month_year.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_month_year.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MAIN};")
        self.btn_next = QToolButton(); self.btn_next.setText(">"); self.btn_next.setFixedSize(30, 30); self.btn_next.setObjectName("CalNavBtn"); self.btn_next.clicked.connect(self.next_month)
        header_layout.addWidget(self.btn_prev); header_layout.addWidget(self.lbl_month_year, 1); header_layout.addWidget(self.btn_next)
        self.grid_container = QWidget(); self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(5, 5, 5, 5); self.grid_layout.setSpacing(5)
        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            lbl = QLabel(day); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl.setStyleSheet(f"color: {COLOR_TEXT_SOFT}; font-weight: bold; font-size: 12px; padding: 5px;"); self.grid_layout.addWidget(lbl, 0, i)
        main_layout.addWidget(self.header_frame); main_layout.addWidget(self.grid_container)
    def refresh_grid(self):
        self.lbl_month_year.setText(self.current_date.strftime("%B %Y"))
        for cell in self.cells: self.grid_layout.removeWidget(cell); cell.deleteLater()
        self.cells.clear(); cal = calendar.Calendar(firstweekday=0)
        for r, week in enumerate(cal.monthdatescalendar(self.current_date.year, self.current_date.month)):
            for c, day in enumerate(week):
                cell = DayCell(day, (day.month == self.current_date.month), self.data_manager)
                if day == self.selected_date: cell.is_selected = True
                cell.clicked.connect(self.on_day_clicked); self.grid_layout.addWidget(cell, r + 1, c); self.cells.append(cell)
    def prev_month(self): self.current_date = (self.current_date.replace(day=1) - timedelta(days=1)).replace(day=1); self.refresh_grid()
    def next_month(self): d = self.current_date; self.current_date = (d.replace(day=1) + timedelta(days=calendar.monthrange(d.year, d.month)[1] + 1)).replace(day=1); self.refresh_grid()
    def on_day_clicked(self, date_obj):
        self.selected_date = date_obj
        if date_obj.month != self.current_date.month: self.current_date = date_obj.replace(day=1)
        self.refresh_grid(); self.dateSelected.emit(date_obj)
    def update_cells(self): [cell.update() for cell in self.cells]

class DailyViewWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__(); self.data_manager = data_manager; layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)
        self.lbl_date = QLabel("..."); self.lbl_date.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.lbl_details = QLabel("Select a date."); self.lbl_details.setWordWrap(True); self.lbl_details.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lbl_details.setStyleSheet("font-size: 14px; line-height: 1.5;"); layout.addWidget(self.lbl_date); layout.addWidget(self.lbl_details, 1)
    def set_date(self, d):
        self.lbl_date.setText(d.strftime("%A, %d %B %Y")); entry = self.data_manager.get_entry(d.strftime("%Y-%m-%d"))
        period_day = self.data_manager.get_period_day_number(d); is_fertile = self.data_manager.is_fertile_window(d)
        moon_age = get_moon_phase(d)
        details = []
        if period_day > 0: details.append(f"🩸 Period Day {period_day}")
        if is_fertile: details.append("🥚 Fertile Window")
        if entry.get('boink'): details.append("❤️ Boink!")
        if entry.get('mood'): details.append(f"<b>Mood:</b> {entry['mood']}")
        details.append(f"{get_moon_icon_char(moon_age)} Moon Age: ~{int(moon_age)} days")
        if entry.get('diary'): details.append(f"\n<b>Diary Entry:</b>\n<i>{entry['diary']}</i>")
        self.lbl_details.setText("<br>".join(details) if details else "No entry for this day.")

class WeeklyViewWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__(); self.data_manager = data_manager; self.day_cells = []
        layout = QGridLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(5)
        for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            lbl = QLabel(day_name); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl.setStyleSheet(f"color: {COLOR_TEXT_SOFT}; font-weight: bold;"); layout.addWidget(lbl, 0, i)
        for i in range(7): cell = DayCell(date.today(), True, self.data_manager); self.day_cells.append(cell); layout.addWidget(cell, 1, i)
    def set_date(self, d):
        start_of_week = d - timedelta(days=d.weekday())
        for i, cell in enumerate(self.day_cells):
            cell.day_date = start_of_week + timedelta(days=i); cell.is_selected = (cell.day_date == d)
            cell.is_current_month = True; cell.update()

# --- MAIN WINDOW ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(APP_NAME); self.resize(1100, 800); self.setWindowOpacity(0.0)
        self.app_icon = QIcon(ICON_FILE) if os.path.exists(ICON_FILE) else QIcon(create_fallback_icon_pixmap())
        self.setWindowIcon(self.app_icon); self.data_manager = DataManager(); self.selected_py_date = date.today()
        self.current_weather_data = {}; self.init_ui(); self.init_tray(); self.load_dashboard_data()
        self.weather_worker = WeatherWorker(); self.weather_worker.finished.connect(self.update_weather_data)
        self.weather_worker.start()

    def showEvent(self, event):
        anim = QPropertyAnimation(self, b"windowOpacity"); anim.setDuration(500); anim.setStartValue(0.0)
        anim.setEndValue(1.0); anim.setEasingCurve(QEasingCurve.Type.OutQuad); anim.start(); super().showEvent(event)

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central); main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(25, 25, 25, 25); main_layout.setSpacing(30)
        
        # Left Column
        left_layout = QVBoxLayout(); left_layout.setSpacing(15)
        lbl_title = QLabel(APP_NAME); lbl_title.setStyleSheet(f"font-size: 36px; font-weight: 800; color: {COLOR_TEXT_MAIN}; margin-bottom: 10px; font-family: 'Segoe UI Black';")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter); left_layout.addWidget(lbl_title)
        self.tabs = QTabWidget(); self.daily_view = DailyViewWidget(self.data_manager); self.weekly_view = WeeklyViewWidget(self.data_manager)
        self.monthly_view = CustomCalendarWidget(self.data_manager); self.yearly_view = QLabel("Yearly view not implemented.")
        self.yearly_view.setAlignment(Qt.AlignmentFlag.AlignCenter); self.monthly_view.dateSelected.connect(self.on_date_selected)
        self.tabs.addTab(self.daily_view, "Daily"); self.tabs.addTab(self.weekly_view, "Weekly")
        self.tabs.addTab(self.monthly_view, "Monthly"); self.tabs.addTab(self.yearly_view, "Yearly"); self.tabs.setCurrentIndex(2)
        cal_container = DashboardCard(QVBoxLayout()); cal_container.layout().setContentsMargins(10, 10, 10, 10); cal_container.layout().addWidget(self.tabs)
        left_layout.addWidget(cal_container)
        lbl_help = QLabel("🩸 Period   🥚 Fertile   ❤️ Boink   ✏️ Note"); lbl_help.setStyleSheet(f"color: {COLOR_TEXT_SOFT}; font-size: 12px; font-weight: 500;")
        lbl_help.setAlignment(Qt.AlignmentFlag.AlignCenter); left_layout.addWidget(lbl_help)
        left_container = QWidget(); left_container.setLayout(left_layout); left_container.setFixedWidth(450)
        
        # Right Column
        right_layout = QVBoxLayout(); right_layout.setSpacing(20)
        header_card_layout = QHBoxLayout(); header_card_layout.setContentsMargins(20, 15, 20, 15)
        info_layout = QVBoxLayout(); self.lbl_dashboard_date = QLabel(""); self.lbl_dashboard_date.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {COLOR_ACCENT_3};")
        self.lbl_moon_phase_name = QLabel(""); self.lbl_moon_phase_name.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_SOFT};")
        info_layout.addWidget(self.lbl_dashboard_date); info_layout.addWidget(self.lbl_moon_phase_name); header_card_layout.addLayout(info_layout); header_card_layout.addStretch()
        self.lbl_big_moon = QLabel("🌑"); self.lbl_big_moon.setStyleSheet("font-size: 52px;"); header_card_layout.addWidget(self.lbl_big_moon); header_card_layout.addSpacing(15)
        self.btn_weather = QPushButton(); self.btn_weather.setObjectName("WeatherBtn"); self.btn_weather.setIconSize(QSize(40, 40)); self.btn_weather.setText("..."); self.btn_weather.setCursor(Qt.CursorShape.PointingHandCursor); self.btn_weather.clicked.connect(self.open_weather_details); header_card_layout.addWidget(self.btn_weather); right_layout.addWidget(DashboardCard(header_card_layout))
        
        # Combined Panel (Image + Prediction)
        pred_layout = QHBoxLayout(); pred_layout.setSpacing(20)
        
        self.drop_image_panel = DropImageLabel()
        self.drop_image_panel.setMinimumHeight(140)
        self.drop_image_panel.imageDropped.connect(self.save_image_reference)
        img_container_layout = QVBoxLayout(); img_container_layout.setContentsMargins(10, 10, 10, 10)
        img_title = QLabel("🖼️ Daily Snapshot"); img_title.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_SOFT}; font-size: 11px;")
        img_container_layout.addWidget(img_title); img_container_layout.addWidget(self.drop_image_panel)
        pred_layout.addWidget(DashboardCard(img_container_layout), 2)
        
        cycle_layout = QVBoxLayout(); cycle_layout.setContentsMargins(20, 20, 20, 20); self.lbl_next_period = QLabel("--"); self.lbl_next_fertile = QLabel("--"); self.lbl_next_period.setStyleSheet(f"font-weight: bold; color: {COLOR_ACCENT_3}; font-size: 16px;"); self.lbl_next_fertile.setStyleSheet(f"font-weight: bold; color: {COLOR_ACCENT_2}; font-size: 16px;"); cycle_layout.addWidget(QLabel("Next Period:")); cycle_layout.addWidget(self.lbl_next_period); cycle_layout.addSpacing(10); cycle_layout.addWidget(QLabel("Fertile Window:")); cycle_layout.addWidget(self.lbl_next_fertile); pred_layout.addWidget(DashboardCard(cycle_layout), 1)
        right_layout.addLayout(pred_layout)
        
        entry_layout = QVBoxLayout(); entry_layout.setContentsMargins(25, 25, 25, 25); entry_layout.setSpacing(20)
        form_layout = QHBoxLayout(); 
        check_col = QVBoxLayout()
        self.chk_period = QCheckBox("Period Started"); 
        
        # Replaced Checkbox with Sticker System
        sticker_box = QVBoxLayout()
        sticker_box.setSpacing(5)
        sticker_box.addWidget(QLabel("Heart Sticker:"))
        self.heart_sticker = StickerHeart()
        sticker_box.addWidget(self.heart_sticker)
        sticker_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        check_col.addWidget(self.chk_period)
        check_col.addLayout(sticker_box)
        
        self.combo_mood = QComboBox(); self.combo_mood.addItems(["", "😡 Angry", "😢 Sad", "😞 Low", "😰 Anxious", "😐 Neutral", "🙂 Calm", "😊 Happy", "😌 Content", "✨ Energized", "🤩 Amazing"]); self.combo_mood.setPlaceholderText("How do you feel?"); form_layout.addLayout(check_col); form_layout.addStretch(); form_layout.addWidget(self.combo_mood, 1); entry_layout.addLayout(form_layout)
        self.txt_notes = QTextEdit(); self.txt_notes.setPlaceholderText("Dear Diary..."); self.txt_notes.setFixedHeight(120); entry_layout.addWidget(self.txt_notes); entry_layout.addSpacing(10)
        btn_save = QPushButton("Save Entry"); btn_save.clicked.connect(self.save_entry); entry_layout.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignRight); entry_card = DashboardCard(entry_layout); right_layout.addWidget(entry_card); right_layout.addStretch()
        main_layout.addWidget(left_container); main_layout.addLayout(right_layout)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self); self.tray_icon.setIcon(self.app_icon); self.tray_icon.setToolTip(APP_NAME); tray_menu = QMenu()
        show = QAction("Open", self); show.triggered.connect(self.show_window); tray_menu.addAction(show); tray_menu.addSeparator()
        quit = QAction("Exit", self); quit.triggered.connect(self.quit_app); tray_menu.addAction(quit)
        self.tray_icon.setContextMenu(tray_menu); self.tray_icon.activated.connect(self.on_tray_click); self.tray_icon.show()

    def on_tray_click(self, r):
        if r == QSystemTrayIcon.ActivationReason.Trigger: self.fade_out_and_hide() if self.isVisible() else self.show_window()
    def show_window(self): self.show(); self.raise_(); self.activateWindow()
    def quit_app(self): self.fade_out_and_close()
    
    def update_weather_data(self, data):
        if not data: self.btn_weather.setText("Offline"); return
        current = data.get('current', {}); _, emoji = interpret_wmo_code(current.get('weather_code', 0))
        self.btn_weather.setText(f"{emoji} {current.get('temperature_2m', 0)}°C"); self.current_weather_data = data

    def open_weather_details(self): WeatherDialog(self.current_weather_data, self).exec()
    def on_date_selected(self, date_obj): self.selected_py_date = date_obj; self.load_dashboard_data()

    def load_dashboard_data(self):
        d = self.selected_py_date; d_str = d.strftime("%Y-%m-%d")
        self.lbl_dashboard_date.setText(d.strftime("%A, %B %d")); moon_age = get_moon_phase(d)
        self.lbl_big_moon.setText(get_moon_icon_char(moon_age)); phase_name = "Waning" if moon_age >= 15 else "Waxing"
        if moon_age < 1 or moon_age > 28.5: phase_name = "New Moon"
        elif 14 < moon_age < 16: phase_name = "Full Moon"
        self.lbl_moon_phase_name.setText(f"{phase_name} ({int(moon_age)} days)")
        
        entry = self.data_manager.get_entry(d_str)
        self.chk_period.setChecked(entry.get('period', False))
        # Removed boink checkbox check here
        self.txt_notes.setText(entry.get('diary', ""))
        mood = entry.get('mood', "")
        self.combo_mood.setCurrentIndex(self.combo_mood.findText(mood) if mood else 0)
        
        image_file = entry.get('image', "")
        if image_file: self.drop_image_panel.display_image(os.path.join(IMAGE_FOLDER, image_file))
        else: self.drop_image_panel.display_image("")
        
        next_p, next_f = self.data_manager.get_next_cycle_prediction()
        self.lbl_next_period.setText(next_p); self.lbl_next_fertile.setText(next_f)
        self.daily_view.set_date(d); self.weekly_view.set_date(d)

    def save_image_reference(self, filename):
        d_str = self.selected_py_date.strftime("%Y-%m-%d")
        self.data_manager.set_entry(d_str, {"image": filename})

    def save_entry(self):
        d_str = self.selected_py_date.strftime("%Y-%m-%d")
        # We preserve the current boink status from data_manager
        current_entry = self.data_manager.get_entry(d_str)
        entry = {
            "period": self.chk_period.isChecked(), 
            "boink": current_entry.get('boink', False), 
            "mood": self.combo_mood.currentText(), 
            "diary": self.txt_notes.toPlainText()
        }
        self.data_manager.set_entry(d_str, entry); self.monthly_view.update_cells(); self.load_dashboard_data()
        btn = self.sender(); orig_text = btn.text(); btn.setText("Saved!")
        QTimer.singleShot(1000, lambda: btn.setText(orig_text))

    def fade_out_and_close(self):
        anim = QPropertyAnimation(self, b"windowOpacity"); anim.setDuration(400); anim.setStartValue(1.0); anim.setEndValue(0.0)
        anim.finished.connect(QApplication.instance().quit); anim.start()
    def fade_out_and_hide(self):
        anim = QPropertyAnimation(self, b"windowOpacity"); anim.setDuration(400); anim.setStartValue(1.0); anim.setEndValue(0.0)
        anim.finished.connect(self.hide); anim.start()
    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            event.ignore(); self.fade_out_and_hide()
            self.tray_icon.showMessage(APP_NAME, "Minimized to tray.", QSystemTrayIcon.MessageIcon.Information, 1000)
        else: event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    socket = QLocalSocket(); socket.connectToServer(INSTANCE_ID)
    if socket.waitForConnected(500):
        QMessageBox.information(None, APP_NAME, "Application is already running.\nCheck your system tray.")
        sys.exit(0)
    else:
        local_server = QLocalServer(); local_server.listen(INSTANCE_ID)
    app.setQuitOnLastWindowClosed(False); app.setStyle("Fusion"); app.setStyleSheet(STYLESHEET)
    font = QFont("Segoe UI"); font.setStyleHint(QFont.StyleHint.SansSerif); app.setFont(font)
    window = MainWindow(); window.show()
    sys.exit(app.exec())