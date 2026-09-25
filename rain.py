import sys
import random
import math
import threading
from PyQt5.QtCore import Qt, QTimer, QPointF, QSharedMemory
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QCursor
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
import pystray
from PIL import Image, ImageDraw

class RaindropsWidget(QWidget):
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

        # 물방울 리스트 초기화 (개수 50개 유지)
        self.raindrops = []
        for _ in range(50):
            self.raindrops.append(self.create_raindrop(initial=True))
            
        # 물결(리플) 효과 리스트
        self.ripples = []

        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rain)
        self.timer.start(20)

        # 시스템 트레이 실행
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def create_raindrop(self, initial=False):
        """물방울 데이터 생성 (개별 낙하 속도를 넓은 범위로 다르게 설정)"""
        base_alpha = random.randint(70, 140)  # 은은하고 맑은 투명도
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-50, -10),
            'vx': 0.0,
            'vy': random.uniform(1.5, 5.5),           # 빗방울마다 속도가 제각각 다르게 적용됨
            'size': random.randint(7, 13),            # 작고 아담한 크기 유지
            'alpha': base_alpha,
            'mx_vx': 0.0,                             # 마우스 회피용 가로 속도
            'mx_vy': 0.0                              # 마우스 회피용 세로 속도
        }

    def update_rain(self):
        """물방울 수직 낙하, 마우스 반경 30 회피 및 바닥 물결 업데이트"""
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx = cursor_local.x()
        my = cursor_local.y()
        
        repel_radius = 30  # 마우스 피하는 반경 30

        for drop in self.raindrops:
            drop['y'] += drop['vy'] + drop['mx_vy']
            drop['x'] += drop['vx'] + drop['mx_vx']
            
            drop['mx_vx'] *= 0.85
            drop['mx_vy'] *= 0.85

            # 마우스와의 거리 계산
            dx = drop['x'] - mx
            dy = drop['y'] - my
            dist = math.hypot(dx, dy)

            # 마우스가 반경 30 이내로 가까워지면 살짝 튕겨나감
            if dist < repel_radius and dist > 0.1:
                force = (1.0 - (dist / repel_radius)) * 2.5
                drop['mx_vx'] += (dx / dist) * force
                drop['mx_vy'] += (dy / dist) * force + 0.1

            # 화면 아래 바닥에 닿으면 위쪽에서 재생성
            if drop['y'] > self.height() - 20:
                if random.random() < 0.3:
                    # 바닥에 떨어질 때 퍼지는 잔잔한 물결(리플) 추가
                    self.ripples.append({
                        'x': drop['x'],
                        'y': random.randint(self.height() - 60, self.height() - 10),
                        'current_r': 2.0,
                        'max_r': random.randint(8, 15),
                        'alpha': random.randint(80, 140)
                    })
                
                new_drop = self.create_raindrop(initial=False)
                drop.update(new_drop)

        # 물결(리플) 애니메이션 업데이트
        for ripple in self.ripples[:]:
            ripple['current_r'] += 0.4
            ripple['alpha'] -= 4
            if ripple['alpha'] <= 0 or ripple['current_r'] >= ripple['max_r']:
                self.ripples.remove(ripple)
                
        self.update()

    def draw_water_drop(self, painter, size):
        """작고 몽글몽글한 이슬방울 모양 드로잉"""
        radius = size / 2.0
        path = QPainterPath()
        
        path.moveTo(0, -radius)
        path.cubicTo(radius * 0.8, -radius * 0.2, radius * 0.9, radius * 0.9, 0, radius)
        path.cubicTo(-radius * 0.9, radius * 0.9, -radius * 0.8, -radius * 0.2, 0, -radius)
        path.closeSubpath()
        
        painter.drawPath(path)
        painter.fillPath(path, painter.brush())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 1. 속도가 제각각 다른 작고 앙증맞은 물방울들 그리기
        for drop in self.raindrops:
            alpha_val = int(drop['alpha'])
            if alpha_val < 3:
                continue

            fill_color = QColor(190, 230, 250, int(alpha_val * 0.75))  # 맑은 하늘빛 물방울 내부
            pen_color = QColor(100, 175, 230, int(alpha_val * 1.2))     # 깔끔한 테두리

            painter.setPen(QPen(pen_color, 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(fill_color))

            painter.save()
            painter.translate(drop['x'], drop['y'])
            
            self.draw_water_drop(painter, drop['size'])
            
            painter.restore()

        # 2. 바닥에 떨어질 때 퍼지는 잔잔한 물결(타원형 리플) 그리기
        for ripple in self.ripples:
            r_alpha = max(0, ripple['alpha'])
            ripple_color = QColor(170, 215, 245, r_alpha)
            
            painter.setPen(QPen(ripple_color, 1.0))
            painter.setBrush(Qt.NoBrush)
            
            rx = ripple['current_r']
            ry = ripple['current_r'] * 0.35
            painter.drawEllipse(QPointF(ripple['x'], ripple['y']), rx, ry)

    def setup_tray(self):
        """시스템 트레이 아이콘 설정"""
        image = Image.new('RGB', (64, 64), color=(230, 240, 250))
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill=(130, 180, 220))

        menu = (pystray.MenuItem('종료(Exit)', self.quit_window),)
        self.icon = pystray.Icon("Raindrops", image, "Raindrops", menu)
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
    shared_memory = QSharedMemory("RaindropsApp_Unique_Key_2026")
    if not shared_memory.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("알림")
        msg.setText("비 내리는 위젯이 이미 실행 중입니다!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)

    widget = RaindropsWidget()
    widget.root_app = app
    widget.show()
    sys.exit(app.exec_())