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
        
        # 마우스 클릭 및 호버 이벤트를 통과시켜 아래 창을 조작할 수 있게 설정
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        self.showFullScreen()

        # 벚꽃잎 리스트 초기화 (쾌적한 개수 50개)
        self.petals = []
        for _ in range(50):
            self.petals.append(self.create_petal(initial=True))
            
        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_petals)
        self.timer.start(20)

        # 시스템 트레이 실행
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def create_petal(self, initial=False):
        """벚꽃잎 데이터 생성 (마우스 회피용 속도 벡터 vx, vy 포함)"""
        base_alpha = random.randint(55, 110)  # 은은하게 비치는 투명도
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.7, 1.8),         # 낙하 속도
            'vx': 0.0,                                 # 마우스 회피 가로 속도
            'vy': 0.0,                                 # 마우스 회피 세로 속도
            'sway_speed': random.uniform(0.015, 0.05), # 좌우 흔들리는 주기
            'sway_amp': random.uniform(15, 35),        # 흔들리는 폭
            'offset_x': random.uniform(0, 100),        # 흔들림 오프셋
            'size': random.randint(12, 22),            # 벚꽃 크기
            'shape_type': random.randint(0, 1),        # 0: 단일 꽃잎, 1: 5잎 벚꽃송이
            'angle': random.uniform(0, 360),           # 회전 각도
            'rot_speed': random.uniform(-1.0, 1.0),    # 회전 속도
            'alpha': base_alpha
        }

    def update_petals(self):
        """벚꽃잎 낙하 및 마우스 반경 30 미세 회피 업데이트"""
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx = cursor_local.x()
        my = cursor_local.y()
        
        repel_radius = 30  # 마우스 피하는 반경 30 설정

        for petal in self.petals:
            petal['y'] += petal['speed'] + petal['vy']
            petal['x'] += petal['vx']
            petal['offset_x'] += petal['sway_speed']
            
            petal['vx'] *= 0.85
            petal['vy'] *= 0.85

            current_x = petal['x'] + math.sin(petal['offset_x']) * petal['sway_amp']

            dx = current_x - mx
            dy = petal['y'] - my
            dist = math.hypot(dx, dy)

            # 마우스가 반경 30 이내로 가까워지면 살짝 튕겨나감
            if dist < repel_radius and dist > 0.1:
                force = (1.0 - (dist / repel_radius)) * 2.5
                petal['vx'] += (dx / dist) * force
                petal['vy'] += (dy / dist) * force + 0.1

            petal['angle'] += petal['rot_speed']
            
            # 화면 아래나 좌우로 벗어나면 위쪽에서 재생성
            if petal['y'] > self.height() + 30 or petal['x'] < -60 or petal['x'] > self.width() + 60:
                new_petal = self.create_petal(initial=False)
                petal.update(new_petal)
                
        self.update()

    def draw_petal_shape(self, painter, size, petal):
        """연분홍빛 벚꽃잎 및 벚꽃송이 드로잉"""
        shape_type = petal.get('shape_type', 0)
        radius = size / 2.0

        if shape_type == 0:
            # 타입 0: 하늘하늘 떨어지는 단일 벚꽃잎
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
            alpha_val = int(petal['alpha'])
            if alpha_val < 3:
                continue

            # 은은하고 맑은 연분홍 벚꽃 컬러
            fill_color = QColor(255, 190, 205, int(alpha_val * 0.75)) 
            pen_color = QColor(255, 140, 165, int(alpha_val * 1.2))     

            painter.setPen(QPen(pen_color, 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(fill_color))
            
            current_x = petal['x'] + math.sin(petal['offset_x']) * petal['sway_amp']

            painter.save()
            painter.translate(current_x, petal['y'])
            painter.rotate(petal['angle'])
            
            self.draw_petal_shape(painter, petal['size'], petal)
            
            painter.restore()

    def setup_tray(self):
        """시스템 트레이 아이콘 설정"""
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

    # 중복 실행 방지 로직
    shared_memory = QSharedMemory("CherryBlossomApp_Unique_Key_2026")
    if not shared_memory.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("알림")
        msg.setText("봄 벚꽃 위젯이 이미 실행 중입니다!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)

    widget = CherryBlossomWidget()
    widget.root_app = app
    widget.show()
    sys.exit(app.exec_())