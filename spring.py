import sys
import random
import math
import threading
from PyQt5.QtCore import Qt, QTimer, QPointF, QSharedMemory
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF, QCursor, QPainterPath
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
import pystray
from PIL import Image, ImageDraw

class CherryBlossomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # 창 설정: 투명하고 항상 위에 위치, 테두리 없음
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.showFullScreen()

        # 벚꽃잎 리스트 초기화
        self.petals = []
        for _ in range(85):
            self.petals.append(self.create_petal(initial=True))
            
        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_petals)
        self.timer.start(20)

        # 시스템 트레이 실행
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def create_petal(self, initial=False):
        """벚꽃잎 데이터 생성 (부드러운 좌우 흔들림 변수 포함)"""
        base_alpha = random.randint(150, 230)
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.8, 2.2),         # 낙하 속도
            'sway_speed': random.uniform(0.02, 0.06),  # 좌우로 하늘하늘 흔들리는 주기
            'sway_amp': random.uniform(10, 30),        # 흔들리는 폭
            'offset_x': random.uniform(0, 100),        # 흔들림 오프셋
            'size': random.randint(12, 24),            # 벚꽃 크기
            'shape_type': random.randint(0, 1),        # 0: 단일 꽃잎, 1: 5잎 벚꽃송이
            'angle': random.uniform(0, 360),           # 회전 각도
            'rot_speed': random.uniform(-1.2, 1.2),    # 회전 속도
            'base_alpha': base_alpha,
            'current_alpha': base_alpha
        }

    def update_petals(self):
        """벚꽃잎 낙하, 하늘하늘 흔들림 및 마우스 근접 시 페이드 아웃 업데이트"""
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx = cursor_local.x()
        my = cursor_local.y()
        
        melt_radius = 110  # 마우스 근처에 오면 사르르 녹아 사라지는 반경

        for petal in self.petals:
            # 1. 아래로 떨어지면서 봄바람에 날리듯 좌우로 하늘하늘 흔들리는 움직임
            petal['y'] += petal['speed']
            petal['offset_x'] += petal['sway_speed']
            current_x = petal['x'] + math.sin(petal['offset_x']) * petal['sway_amp']

            # 2. 마우스와의 거리 계산
            dx = current_x - mx
            dy = petal['y'] - my
            dist = math.hypot(dx, dy)

            # --- [페이드 아웃 효과] 마우스에 가까워지면 사르르 사라짐 ---
            if dist < melt_radius:
                target_alpha = 0
                fade_rate = 0.15
                petal['current_alpha'] += (target_alpha - petal['current_alpha']) * fade_rate
            else:
                fade_rate = 0.08
                petal['current_alpha'] += (petal['base_alpha'] - petal['current_alpha']) * fade_rate

            # 회전각 업데이트
            petal['angle'] += petal['rot_speed']
            
            # 화면 아래로 내려가면 위쪽에서 새 벚꽃잎으로 재생성
            if petal['y'] > self.height() + 30:
                new_petal = self.create_petal(initial=False)
                petal.update(new_petal)
                
        self.update()

    def draw_petal_shape(self, painter, size, petal):
        """연분홍빛 벚꽃잎 및 벚꽃송이 드로잉"""
        shape_type = petal.get('shape_type', 0)
        radius = size / 2.0

        if shape_type == 0:
            # 타입 0: 하늘하늘 떨어지는 단일 벚꽃잎 (타원/눈물방울 형태)
            path = QPainterPath()
            path.moveTo(0, -radius)
            path.quadTo(radius * 0.7, -radius * 0.3, 0, radius)
            path.quadTo(-radius * 0.7, -radius * 0.3, 0, -radius)
            painter.drawPath(path)
            painter.fillPath(path, painter.brush())
            
        else:
            # 타입 1: 5개의 꽃잎이 모인 귀여운 벚꽃송이
            for i in range(5):
                painter.save()
                painter.rotate(i * 72)
                petal_path = QPainterPath()
                petal_path.addEllipse(QPointF(0, -radius * 0.5), radius * 0.35, radius * 0.5)
                painter.drawPath(petal_path)
                painter.fillPath(petal_path, painter.brush())
                painter.restore()
                
            # 중앙의 작은 암술/수술 포인트 장식
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 100, 130, painter.pen().color().alpha()))
            painter.drawEllipse(QPointF(0, 0), radius * 0.15, radius * 0.15)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for petal in self.petals:
            alpha_val = int(petal['current_alpha'])
            if alpha_val < 3:
                continue

            # 화사하고 부드러운 연분홍 벚꽃 컬러
            fill_color = QColor(255, 183, 197, int(alpha_val * 0.75)) # 연분홍 채우기
            pen_color = QColor(255, 140, 160, alpha_val)             # 테두리 선 색상

            painter.setPen(QPen(pen_color, 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(fill_color))
            
            # 흔들림이 반영된 현재 x 위치 계산
            current_x = petal['x'] + math.sin(petal['offset_x']) * petal['sway_amp']

            painter.save()
            painter.translate(current_x, petal['y'])
            painter.rotate(petal['angle'])
            
            self.draw_petal_shape(painter, petal['size'], petal)
            
            painter.restore()

    def setup_tray(self):
        """시스템 트레이 아이콘 설정 (봄 느낌의 핑크빛 아이콘)"""
        image = Image.new('RGB', (64, 64), color=(255, 240, 245))
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill=(255, 150, 170))

        menu = (pystray.MenuItem('종료(Exit)', self.quit_window),)
        self.icon = pystray.Icon("CherryBlossom", image, "CherryBlossom", menu)
        self.icon.run()

    def quit_window(self):
        """프로그램 종료"""
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root_app.quit()
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- 중복 실행 방지(Single Instance) 로직 ---
    shared_memory = QSharedMemory("CherryBlossomApp_Unique_Key_2026")
    
    if not shared_memory.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("알림")
        msg.setText("봄 벚꽃 위젯이 이미 실행 중입니다!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)
    # ----------------------------------------

    widget = CherryBlossomWidget()
    widget.root_app = app
    widget.show()
    sys.exit(app.exec_())