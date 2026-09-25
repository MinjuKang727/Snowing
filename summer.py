import sys
import random
import math
import threading
from PyQt5.QtCore import Qt, QTimer, QPointF, QSharedMemory
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QRadialGradient, QCursor
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
import pystray
from PIL import Image, ImageDraw

class SummerFirefliesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # 창 설정: 투명하고 항상 위에 위치, 테두리 없음
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.showFullScreen()

        # 반딧불이 리스트 초기화
        self.fireflies = []
        for _ in range(45):
            self.fireflies.append(self.create_firefly(initial=True))
            
        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_fireflies)
        self.timer.start(20)

        # 시스템 트레이 실행
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def create_firefly(self, initial=False):
        """반딧불이 데이터 생성"""
        base_alpha = random.randint(230, 255)  # 최대 밝기를 꽉 채워 선명하게 설정
        return {
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(self.height(), self.height() + 50),
            'vx': random.uniform(-0.7, 0.7),
            'vy': random.uniform(-1.4, -0.5),
            'sway_freq': random.uniform(0.025, 0.06),
            'sway_offset': random.uniform(0, 100),
            'size': random.randint(18, 26),
            'flash_speed': random.uniform(0.1, 0.2),
            'flash_val': random.uniform(0, math.pi),
            'base_alpha': base_alpha,
            'current_alpha': base_alpha
        }

    def update_fireflies(self):
        """반딧불이 유영, 활발한 움직임 및 페이드 아웃 업데이트"""
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx = cursor_local.x()
        my = cursor_local.y()
        
        melt_radius = 120

        for f in self.fireflies:
            f['sway_offset'] += f['sway_freq']
            f['x'] += f['vx'] + math.sin(f['sway_offset']) * 1.2
            f['y'] += f['vy']

            f['flash_val'] += f['flash_speed']
            flash_factor = (math.sin(f['flash_val']) + 1.0) / 2.0
            flash_factor = flash_factor ** 2  
            
            dynamic_base_alpha = f['base_alpha'] * (0.2 + 0.8 * flash_factor)

            dx = f['x'] - mx
            dy = f['y'] - my
            dist = math.hypot(dx, dy)

            if dist < melt_radius:
                target_alpha = 0
                fade_rate = 0.15
                f['current_alpha'] += (target_alpha - f['current_alpha']) * fade_rate
            else:
                fade_rate = 0.08
                f['current_alpha'] += (dynamic_base_alpha - f['current_alpha']) * fade_rate

            if f['y'] < -40 or f['x'] < -50 or f['x'] > self.width() + 50:
                new_f = self.create_firefly(initial=False)
                new_f['y'] = self.height() + 30
                f.update(new_f)
                
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for f in self.fireflies:
            alpha_val = int(f['current_alpha'])
            if alpha_val < 3:
                continue

            radius = f['size'] / 2.0

            # 1. 주변 빛무리를 초록빛 대신 화사하고 따스한 [황금빛/노란빛 오라]로 변경
            gradient = QRadialGradient(QPointF(f['x'], f['y']), radius)
            gradient.setColorAt(0.0, QColor(255, 255, 180, int(alpha_val * 0.95))) # 중심부 아주 환한 연노랑
            gradient.setColorAt(0.5, QColor(255, 220, 80, int(alpha_val * 0.5)))   # 따스한 골드 옐로우
            gradient.setColorAt(1.0, QColor(255, 180, 20, 0))                      # 바깥쪽으로 부드럽게 소멸

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(QPointF(f['x'], f['y']), radius, radius)

            # 2. 중심부 코어를 순백색에 가까운 아주 밝은 노란빛으로 극대화
            core_radius = radius * 0.35
            core_gradient = QRadialGradient(QPointF(f['x'], f['y']), core_radius)
            core_gradient.setColorAt(0.0, QColor(255, 255, 255, alpha_val))       # 순백색 코어
            core_gradient.setColorAt(1.0, QColor(255, 245, 100, int(alpha_val * 0.9))) # 밝고 선명한 노란빛

            painter.setBrush(QBrush(core_gradient))
            painter.drawEllipse(QPointF(f['x'], f['y']), core_radius, core_radius)

    def setup_tray(self):
        """시스템 트레이 아이콘 설정 (노란빛 반딧불이 테마)"""
        image = Image.new('RGB', (64, 64), color=(255, 255, 240))
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill=(255, 220, 50))

        menu = (pystray.MenuItem('종료(Exit)', self.quit_window),)
        self.icon = pystray.Icon("SummerFireflies", image, "SummerFireflies", menu)
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
    shared_memory = QSharedMemory("SummerFirefliesApp_Unique_Key_2026")
    if not shared_memory.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("알림")
        msg.setText("여름 반딧불이 위젯이 이미 실행 중입니다!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)

    widget = SummerFirefliesWidget()
    widget.root_app = app
    widget.show()
    sys.exit(app.exec_())