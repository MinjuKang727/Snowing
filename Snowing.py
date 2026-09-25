import sys
import random
import math
import threading
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
from PyQt5.QtWidgets import QApplication, QWidget
import pystray
from PIL import Image, ImageDraw

class SnowflakeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # 창 설정: 투명하고 항상 위에 위치, 테두리 없음
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.showFullScreen()
        
        # 마우스 클릭 투과 설정 (Windows API)
        try:
            import ctypes
            hwnd = int(self.winId())
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, -20, ex_style | 0x00080000 | 0x00000020
            )
        except Exception:
            pass

        # 눈송이 리스트 초기화 (더 가벼운 느낌을 위해 개수 100개로 풍성하게 유지)
        self.snowflakes = []
        for _ in range(100):
            self.snowflakes.append(self.create_snowflake(initial=True))
            
        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_snow)
        self.timer.start(20)

        # 시스템 트레이 실행
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def create_snowflake(self, initial=False):
        """눈송이 데이터 생성 (크기를 5~14 픽셀로 아주 작게 축소)"""
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.5, 1.8),
            'size': random.randint(5, 14),           # 초미세 크기로 조정
            'shape_type': random.randint(0, 3),      # 4가지의 다양한 결정 패턴
            'angle': random.uniform(0, 360),           # 회전 각도
            'rot_speed': random.uniform(-0.7, 0.7),    # 회전 속도
            'alpha': random.randint(130, 210)          # 은은한 투명도
        }

    def update_snow(self):
        """눈송이 위치 및 회전각 업데이트"""
        for flake in self.snowflakes:
            flake['y'] += flake['speed']
            flake['angle'] += flake['rot_speed']
            
            # 화면 아래로 내려가면 위쪽에서 재생성
            if flake['y'] > self.height() + 30:
                new_flake = self.create_snowflake(initial=False)
                flake.update(new_flake)
                
        self.update()

    def draw_snowflake_shape(self, painter, size, flake):
        """매우 작으면서도 결정의 형태를 유지하는 초미세 드로잉"""
        radius = size / 2.0
        shape_type = flake.get('shape_type', 0)

        # 타입 3: 미니 육각형 판상 결정
        if shape_type == 3:
            plate_poly = QPolygonF()
            for j in range(6):
                deg = j * 60
                rad = math.radians(deg)
                plate_poly.append(QPointF(radius * 0.7 * math.cos(rad), radius * 0.7 * math.sin(rad)))
            painter.drawPolygon(plate_poly)
            
            inner_poly = QPolygonF()
            for j in range(6):
                deg = j * 60
                rad = math.radians(deg)
                inner_poly.append(QPointF(radius * 0.3 * math.cos(rad), radius * 0.3 * math.sin(rad)))
            painter.drawPolygon(inner_poly)
            
            for j in range(6):
                deg = j * 60
                rad = math.radians(deg)
                painter.drawLine(QPointF(radius * 0.3 * math.cos(rad), radius * 0.3 * math.sin(rad)),
                                 QPointF(radius * 0.7 * math.cos(rad), radius * 0.7 * math.sin(rad)))
            return

        # 0, 1, 2 타입: 6방향 대칭 구조
        for i in range(6):
            painter.save()
            painter.rotate(i * 60)

            # 1. 메인 줄기
            painter.drawLine(QPointF(0, 0), QPointF(0, -radius))

            # 2. 아주 작은 크기에 맞춘 심플한 세부 장식
            if shape_type == 0:
                y_pos = -radius * 0.5
                b_len = radius * 0.4
                painter.drawLine(QPointF(0, y_pos), QPointF(b_len, y_pos - b_len * 0.5))
                painter.drawLine(QPointF(0, y_pos), QPointF(-b_len, y_pos - b_len * 0.5))

            elif shape_type == 1:
                end_pt = QPointF(0, -radius)
                painter.drawLine(end_pt, QPointF(radius * 0.25, -radius - radius * 0.2))
                painter.drawLine(end_pt, QPointF(-radius * 0.25, -radius - radius * 0.2))

            elif shape_type == 2:
                y_pos = -radius * 0.5
                w = radius * 0.25
                painter.drawLine(QPointF(0, y_pos), QPointF(w, y_pos - w))
                painter.drawLine(QPointF(w, y_pos - w), QPointF(0, y_pos - w * 2))
                painter.drawLine(QPointF(0, y_pos), QPointF(-w, y_pos - w))
                painter.drawLine(QPointF(-w, y_pos - w), QPointF(0, y_pos - w * 2))

            painter.restore()

        # 3. 중앙 육각형 코어 장식
        if shape_type != 3:
            core_r = radius * 0.22
            core_poly = QPolygonF()
            for j in range(6):
                deg = j * 60
                rad = math.radians(deg)
                core_poly.append(QPointF(core_r * math.cos(rad), core_r * math.sin(rad)))
            painter.drawPolygon(core_poly)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for flake in self.snowflakes:
            # 펜 두께를 0.8로 더욱 얇고 섬세하게 설정
            pen = QPen(QColor(235, 245, 255, flake['alpha']), 0.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            painter.save()
            painter.translate(flake['x'], flake['y'])
            painter.rotate(flake['angle'])
            
            self.draw_snowflake_shape(painter, flake['size'], flake)
            
            painter.restore()

    def setup_tray(self):
        """시스템 트레이 아이콘 설정"""
        image = Image.new('RGB', (64, 64), color=(255, 255, 255))
        dc = ImageDraw.Draw(image)
        dc.rectangle((16, 16, 48, 48), fill=(0, 150, 255))

        menu = (pystray.MenuItem('종료(Exit)', self.quit_window),)
        self.icon = pystray.Icon("Snowing", image, "Snowing", menu)
        self.icon.run()

    def quit_window(self):
        """프로그램 종료"""
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root_app.quit()
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = SnowflakeWidget()
    widget.root_app = app
    widget.show()
    sys.exit(app.exec_())