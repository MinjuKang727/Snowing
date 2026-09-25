import sys
import random
import math
import threading
from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF, QCursor
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

        # 눈송이 리스트 초기화
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
        """눈송이 데이터 생성 (기본 낙하 속도 및 투명도 설정)"""
        base_alpha = random.randint(130, 210)
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.5, 1.8),
            'size': random.randint(5, 14),
            'shape_type': random.randint(0, 3),
            'angle': random.uniform(0, 360),
            'rot_speed': random.uniform(-0.7, 0.7),
            'base_alpha': base_alpha,     # 본래의 은은한 투명도
            'current_alpha': base_alpha   # 마우스 근접 시 변하는 투명도 (페이드 아웃용)
        }

    def update_snow(self):
        """눈송이의 자연스러운 낙하와 마우스 근접 시 페이드 아웃(녹음) 효과 업데이트"""
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx = cursor_local.x()
        my = cursor_local.y()
        
        melt_radius = 200  # 눈이 서서히 녹아 사라지는(페이드 아웃) 반경

        for flake in self.snowflakes:
            # 1. 오직 아래로만 차분하게 떨어지는 기본 움직임
            flake['y'] += flake['speed']

            # 2. 마우스와의 거리 계산
            dx = flake['x'] - mx
            dy = flake['y'] - my
            dist = math.hypot(dx, dy)

            # --- [페이드 아웃/녹음 효과] 마우스에 가까워지면 투명도가 0으로 서서히 감소 ---
            if dist < melt_radius:
                target_alpha = 0
                fade_rate = 0.15 # 녹아내리는 속도
                flake['current_alpha'] += (target_alpha - flake['current_alpha']) * fade_rate
            else:
                # 마우스에서 멀어지면 원래 투명도로 서서히 복귀
                fade_rate = 0.08
                flake['current_alpha'] += (flake['base_alpha'] - flake['current_alpha']) * fade_rate

            # 회전각 업데이트
            flake['angle'] += flake['rot_speed']
            
            # 화면 아래로 내려가거나 좌우로 크게 벗어나면 위쪽에서 새 눈송이로 재생성
            if flake['y'] > self.height() + 30:
                new_flake = self.create_snowflake(initial=False)
                flake.update(new_flake)
                
        self.update()

    def draw_snowflake_shape(self, painter, size, flake):
        """초미세 눈 결정 드로잉"""
        radius = size / 2.0
        shape_type = flake.get('shape_type', 0)

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

        for i in range(6):
            painter.save()
            painter.rotate(i * 60)
            painter.drawLine(QPointF(0, 0), QPointF(0, -radius))

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
            alpha_val = int(flake['current_alpha'])
            if alpha_val < 3:
                continue

            pen = QPen(QColor(235, 245, 255, alpha_val), 0.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
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