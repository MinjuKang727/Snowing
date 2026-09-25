import sys
import random
import math
import threading
from PyQt5.QtCore import Qt, QTimer, QPointF, QSharedMemory
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF, QCursor, QPainterPath
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
import pystray
from PIL import Image, ImageDraw

class AutumnLeavesWidget(QWidget):
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

        # 낙엽 수 25개 유지
        self.leaves = []
        for _ in range(25):
            self.leaves.append(self.create_leaf(initial=True))
            
        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_leaves)
        self.timer.start(20)

        # 시스템 트레이 실행
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def create_leaf(self, initial=False):
        """낙엽 데이터 생성 (차분한 낙하 및 반투명 감성)"""
        base_alpha = random.randint(50, 95)
        color_type = random.choice(['maple_orange', 'maple_red', 'ginkgo_yellow'])
        
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.7, 2.0),
            'vx': 0.0,
            'vy': 0.0,
            'sway_speed': random.uniform(0.015, 0.05),
            'sway_amp': random.uniform(15, 40),
            'offset_x': random.uniform(0, 100),
            'size': random.randint(16, 26),
            'shape_type': random.randint(0, 2),  # 0: 단풍잎, 1: 170도 넓은 은행잎, 2: 타원 낙엽
            'color_type': color_type,
            'angle': random.uniform(0, 360),
            'rot_speed': random.uniform(-1.2, 1.2),
            'alpha': base_alpha
        }

    def update_leaves(self):
        """낙엽 낙하 및 마우스 반경 10 미세 회피 업데이트"""
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx = cursor_local.x()
        my = cursor_local.y()
        
        repel_radius = 30  # 마우스 피하는 반경을 10으로 설정

        for leaf in self.leaves:
            leaf['y'] += leaf['speed'] + leaf['vy']
            leaf['x'] += leaf['vx']
            leaf['offset_x'] += leaf['sway_speed']
            
            leaf['vx'] *= 0.85
            leaf['vy'] *= 0.85

            current_x = leaf['x'] + math.sin(leaf['offset_x']) * leaf['sway_amp']

            dx = current_x - mx
            dy = leaf['y'] - my
            dist = math.hypot(dx, dy)

            # 마우스가 반경 10 이내로 아주 가까워지면 살짝 튕겨나감
            if dist < repel_radius and dist > 0.1:
                force = (1.0 - (dist / repel_radius)) * 2.5
                leaf['vx'] += (dx / dist) * force
                leaf['vy'] += (dy / dist) * force + 0.1

            leaf['angle'] += leaf['rot_speed']
            
            # 화면 아래로 내려가면 위쪽에서 다시 재생성
            if leaf['y'] > self.height() + 30 or leaf['x'] < -60 or leaf['x'] > self.width() + 60:
                new_leaf = self.create_leaf(initial=False)
                leaf.update(new_leaf)
                
        self.update()

    def draw_leaf_shape(self, painter, size, leaf):
        """일러스트풍의 아기자기한 낙엽 형태 드로잉"""
        shape_type = leaf.get('shape_type', 0)
        radius = size / 2.0

        if shape_type == 0:
            # 0: 귀여운 별모양 단풍잎
            path = QPainterPath()
            path.moveTo(0, -radius)
            path.quadTo(radius * 0.3, -radius * 0.5, radius * 0.9, -radius * 0.5)
            path.quadTo(radius * 0.4, 0, radius * 0.8, radius * 0.8)
            path.quadTo(0, radius * 0.4, -radius * 0.8, radius * 0.8)
            path.quadTo(-radius * 0.4, 0, -radius * 0.9, -radius * 0.5)
            path.quadTo(-radius * 0.3, -radius * 0.5, 0, -radius)
            path.closeSubpath()
            
            painter.drawPath(path)
            painter.fillPath(path, painter.brush())

            painter.setPen(QPen(painter.pen().color(), 1.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(0, radius * 0.4), QPointF(0, radius * 0.8))

        elif shape_type == 1:
            # 1: 각도가 약 170도로 시원하게 넓게 퍼지는 클래식 부채꼴 은행잎[cite: 5, 6, 7]
            path = QPainterPath()
            path.moveTo(0, radius * 0.85)
            
            path.cubicTo(-radius * 0.4, radius * 0.4, -radius * 1.8, -radius * 0.1, -radius * 2.1, -radius * 0.6)
            path.cubicTo(-radius * 1.4, -radius * 1.1, -radius * 0.4, -radius * 0.9, 0, -radius * 0.3)
            path.cubicTo(radius * 0.4, -radius * 0.9, radius * 1.4, -radius * 1.1, radius * 2.1, -radius * 0.6)
            path.cubicTo(radius * 1.8, -radius * 0.1, radius * 0.4, radius * 0.4, 0, radius * 0.85)
            
            path.closeSubpath()
            
            painter.drawPath(path)
            painter.fillPath(path, painter.brush())

            # 은행잎 줄기
            painter.setPen(QPen(painter.pen().color(), 1.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(0, radius * 0.85), QPointF(0, radius * 1.25))

        else:
            # 2: 동글길쭉한 감성 낙엽
            path = QPainterPath()
            path.moveTo(0, radius)
            path.cubicTo(-radius * 0.8, radius * 0.5, -radius * 0.8, -radius * 0.8, 0, -radius)
            path.cubicTo(radius * 0.8, -radius * 0.8, radius * 0.8, radius * 0.5, 0, radius)
            path.closeSubpath()
            
            painter.drawPath(path)
            painter.fillPath(path, painter.brush())

            painter.setPen(QPen(painter.pen().color(), 1.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(0, radius * 0.8), QPointF(0, -radius * 0.6))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for leaf in self.leaves:
            alpha_val = int(leaf['alpha'])
            if alpha_val < 3:
                continue

            c_type = leaf.get('color_type', 'maple_orange')
            if c_type == 'maple_orange':
                fill_color = QColor(235, 130, 40, int(alpha_val * 0.7))
                pen_color = QColor(160, 75, 15, int(alpha_val * 1.2))
            elif c_type == 'maple_red':
                fill_color = QColor(215, 75, 45, int(alpha_val * 0.7))
                pen_color = QColor(140, 35, 15, int(alpha_val * 1.2))
            else: # 은행잎 노란색
                fill_color = QColor(250, 210, 50, int(alpha_val * 0.7))
                pen_color = QColor(175, 135, 15, int(alpha_val * 1.2))

            painter.setPen(QPen(pen_color, 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(fill_color))
            
            current_x = leaf['x'] + math.sin(leaf['offset_x']) * leaf['sway_amp']

            painter.save()
            painter.translate(current_x, leaf['y'])
            painter.rotate(leaf['angle'])
            
            self.draw_leaf_shape(painter, leaf['size'], leaf)
            
            painter.restore()

    def setup_tray(self):
        """시스템 트레이 아이콘 설정"""
        image = Image.new('RGB', (64, 64), color=(255, 248, 240))
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill=(220, 90, 30))

        menu = (pystray.MenuItem('종료(Exit)', self.quit_window),)
        self.icon = pystray.Icon("AutumnLeaves", image, "AutumnLeaves", menu)
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
    shared_memory = QSharedMemory("AutumnLeavesApp_Unique_Key_2026")
    if not shared_memory.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("알림")
        msg.setText("가을 낙엽 위젯이 이미 실행 중입니다!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)

    widget = AutumnLeavesWidget()
    widget.root_app = app
    widget.show()
    sys.exit(app.exec_())