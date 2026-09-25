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
        """눈송이 데이터 생성 (위치 x, y 및 속도 벡터 vx, vy 포함)"""
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.5, 1.8),
            'vx': 0.0,  # 바람에 의해 밀려나는 가로 속도
            'vy': 0.0,  # 바람에 의해 밀려나는 세로 속도
            'size': random.randint(5, 14),
            'shape_type': random.randint(0, 3),
            'angle': random.uniform(0, 360),
            'rot_speed': random.uniform(-0.7, 0.7),
            'alpha': random.randint(130, 210)
        }

    def update_snow(self):
        """눈송이 낙하 및 넓은 반경에서 부드럽게 퍼지는 바람 상호작용 업데이트"""
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx = cursor_local.x()
        my = cursor_local.y()
        
        # 반경을 넓게 설정 (예: 180픽셀)
        repel_radius = 180  

        for flake in self.snowflakes:
            # 1. 기본 떨어지는 움직임 + 바람 속도 적용
            flake['y'] += flake['speed'] + flake['vy']
            flake['x'] += flake['vx']
            
            # 밀려난 속도는 서서히 감쇠 (저항력)
            flake['vx'] *= 0.88
            flake['vy'] *= 0.88

            # 2. 마우스와의 거리 계산 (넓은 반경 바람 효과)
            dx = flake['x'] - mx
            dy = flake['y'] - my
            dist = math.hypot(dx, dy)

            if dist < repel_radius and dist > 0.1:
                # 멀리서부터 부드럽게 밀려나도록 세밀한 힘 계산
                force = (1.0 - (dist / repel_radius)) * 2.8
                # 마우스 반대 방향으로 밀어내기 + 아래로 살짝 흘러내리는 느낌 추가
                flake['vx'] += (dx / dist) * force
                flake['vy'] += (dy / dist) * force * 0.5 + 0.1

            # 회전각 업데이트
            flake['angle'] += flake['rot_speed']
            
            # 화면 아래로 내려가거나 좌우로 크게 벗어나면 위쪽에서 새 눈송이로 재생성
            if flake['y'] > self.height() + 30 or flake['x'] < -60 or flake['x'] > self.width() + 60:
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