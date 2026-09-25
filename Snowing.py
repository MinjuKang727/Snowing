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

        # 눈송이 리스트 초기화
        self.snowflakes = []
        for _ in range(75):
            self.snowflakes.append(self.create_snowflake(initial=True))
            
        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_snow)
        self.timer.start(20)

        # 시스템 트레이 실행
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def create_snowflake(self, initial=False):
        """눈송이 데이터 생성 (다양한 타입 및 크기 부여)"""
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-60, -10),
            'speed': random.uniform(0.7, 2.2),
            'size': random.randint(22, 48),          # 결정 모양이 잘 보이도록 크기 설정
            'shape_type': random.randint(0, 3),     # 4가지의 다양한 결정 패턴
            'angle': random.uniform(0, 360),          # 회전 각도
            'rot_speed': random.uniform(-0.4, 0.4),   # 회전 속도
            'alpha': random.randint(160, 240)         # 은은한 투명도
        }

    def update_snow(self):
        """눈송이 위치 및 회전각 업데이트"""
        for flake in self.snowflakes:
            flake['y'] += flake['speed']
            flake['angle'] += flake['rot_speed']
            
            # 화면 아래로 내려가면 위쪽에서 재생성
            if flake['y'] > self.height() + 50:
                new_flake = self.create_snowflake(initial=False)
                flake.update(new_flake)
                
        self.update()

    def draw_snowflake_shape(self, painter, size, flake):
        """사진 속 결정들(덴드라이트, 판상형, 복합형)을 모사한 기하학적 드로잉"""
        radius = size / 2.0
        shape_type = flake.get('shape_type', 0)

        # 타입 3: 육각형 판상 결정 (Hexagonal Plate - 사진 하단 중앙 같은 형태)[cite: 9]
        if shape_type == 3:
            plate_poly = QPolygonF()
            for j in range(6):
                deg = j * 60
                rad = math.radians(deg)
                plate_poly.append(QPointF(radius * 0.7 * math.math.cos(rad) if hasattr(math, 'math') else radius * 0.7 * math.cos(rad), 
                                          radius * 0.7 * math.sin(rad)))
            # 외곽 육각형
            painter.drawPolygon(plate_poly)
            
            # 내부 장식 육각형 라인
            inner_poly = QPolygonF()
            for j in range(6):
                deg = j * 60
                rad = math.radians(deg)
                inner_poly.append(QPointF(radius * 0.3 * math.cos(rad), radius * 0.3 * math.sin(rad)))
            painter.drawPolygon(inner_poly)
            
            # 꼭짓점 연결 선
            for j in range(6):
                deg = j * 60
                rad = math.radians(deg)
                painter.drawLine(QPointF(radius * 0.3 * math.cos(rad), radius * 0.3 * math.sin(rad)),
                                 QPointF(radius * 0.7 * math.cos(rad), radius * 0.7 * math.sin(rad)))
            return

        # 0, 1, 2 타입: 6방향 대칭 구조의 나뭇가지 및 복합 결정
        for i in range(6):
            painter.save()
            painter.rotate(i * 60)

            # 1. 메인 줄기
            painter.drawLine(QPointF(0, 0), QPointF(0, -radius))

            # 2. 패턴별 세부 장식
            if shape_type == 0:
                # 촘촘하고 세밀한 덴드라이트(깃털)형[cite: 9]
                for pos_ratio in [0.3, 0.5, 0.7, 0.85]:
                    b_len = radius * (0.32 * (1 - pos_ratio * 0.4))
                    y_pos = -radius * pos_ratio
                    painter.drawLine(QPointF(0, y_pos), QPointF(b_len, y_pos - b_len * 0.5))
                    painter.drawLine(QPointF(0, y_pos), QPointF(-b_len, y_pos - b_len * 0.5))

            elif shape_type == 1:
                # 끝부분이 넓게 퍼지는 꽃잎/방패 형태의 복합 결정[cite: 9, 10]
                mid_pos = -radius * 0.6
                painter.drawLine(QPointF(0, mid_pos), QPointF(radius * 0.25, mid_pos - radius * 0.2))
                painter.drawLine(QPointF(0, mid_pos), QPointF(-radius * 0.25, mid_pos - radius * 0.2))
                
                # 끝단 뾰족한 장식
                end_pt = QPointF(0, -radius)
                painter.drawLine(end_pt, QPointF(radius * 0.12, -radius - radius * 0.25))
                painter.drawLine(end_pt, QPointF(-radius * 0.12, -radius - radius * 0.25))

            elif shape_type == 2:
                # 다이아몬드/화살촉 장식이 반복되는 화려한 결정[cite: 9]
                for pos_ratio in [0.45, 0.75]:
                    y_pos = -radius * pos_ratio
                    w = radius * 0.14
                    painter.drawLine(QPointF(0, y_pos), QPointF(w, y_pos - w * 0.8))
                    painter.drawLine(QPointF(w, y_pos - w * 0.8), QPointF(0, y_pos - w * 1.6))
                    painter.drawLine(QPointF(0, y_pos), QPointF(-w, y_pos - w * 0.8))
                    painter.drawLine(QPointF(-w, y_pos - w * 0.8), QPointF(0, y_pos - w * 1.6))

            painter.restore()

        # 3. 중앙 육각형 코어(핵) 장식
        if shape_type != 3:
            core_r = radius * 0.16
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
            pen = QPen(QColor(235, 245, 255, flake['alpha']), 1.3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
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