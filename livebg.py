import sys
import random
import math
from PyQt5.QtCore import Qt, QTimer, QPointF, QSharedMemory
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF, QCursor, QPainterPath, QRadialGradient, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction, QMessageBox

class UnifiedSeasonsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_theme = 'snow'  # 기본 테마: 겨울(눈)
        self.initUI()
        
    def initUI(self):
        # 창 설정: 투명하고 항상 위에 위치, 테두리 없음, 마우스 클릭 통과
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.showFullScreen()

        self.particles = []
        self.ripples = []
        self.change_theme('snow')

        # 애니메이션 타이머 (약 50fps)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(20)

        # 시스템 트레이 아이콘 설정
        self.setup_tray()

    def setup_tray(self):
        # 메모리 상에서 직접 트레이 아이콘용 픽스맵 생성
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QBrush(QColor(80, 150, 220)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(16, 16, 32, 32)
        painter.end()

        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self)

        # 툴팁 설정 코드
        self.tray_icon.setToolTip("LiveBg")
        
        # 순정 컨텍스트 메뉴 생성
        self.tray_menu = QMenu()
        self.setup_menu_actions()
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # [핵심 최적화] 프로그램이 켜지자마자 백그라운드에서 메뉴를 미리 강제로 싹 렌더링해 둡니다.
        # 이렇게 하면 나중에 사용자가 처음 클릭할 때 멈칫거리는 딜레이가 사라집니다!
        self.tray_menu.ensurePolished()
        
        # 트레이 아이콘 클릭 시 메뉴 팝업 연결
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def setup_menu_actions(self):
        themes = [
            ('🌸 봄 (Cherry Blossom)', 'spring'),
            ('🌿 여름 (Summer Leaves)', 'summer_leaves'),
            ('✨ 반딧불이 (Fireflies)', 'fireflies'),
            ('🍁 가을 (Autumn Leaves)', 'autumn'),
            ('❄️ 겨울 (Snowing)', 'snow'),
            ('🌧️ 비 (Raindrops)', 'rain')
        ]

        for text, theme_key in themes:
            action = QAction(text, self)
            action.triggered.connect(lambda checked, tk=theme_key: self.change_theme(tk))
            self.tray_menu.addAction(action)

        self.tray_menu.addSeparator()
        
        exit_action = QAction('❌ 프로그램 종료', self)
        exit_action.triggered.connect(self.quit_window)
        self.tray_menu.addAction(exit_action)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.Context or reason == QSystemTrayIcon.DoubleClick:
            # 팝업이 뜰 때 메인 이벤트 루프를 방해하지 않도록 비동기로 호출
            QTimer.singleShot(0, lambda: self.tray_menu.popup(QCursor.pos()))

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.particles.clear()
        self.ripples.clear()

        if theme_name == 'snow':
            for _ in range(90):
                self.particles.append(self.create_snowflake(initial=True))
        elif theme_name == 'spring':
            for _ in range(45):
                self.particles.append(self.create_petal(initial=True))
        elif theme_name == 'summer_leaves':
            for _ in range(35):
                self.particles.append(self.create_summer_leaf(initial=True))
        elif theme_name == 'fireflies':
            for _ in range(25):
                self.particles.append(self.create_firefly(initial=True))
        elif theme_name == 'autumn':
            for _ in range(25):
                self.particles.append(self.create_leaf(initial=True))
        elif theme_name == 'rain':
            for _ in range(45):
                self.particles.append(self.create_raindrop(initial=True))

    def create_snowflake(self, initial=False):
        base_alpha = random.randint(45, 110)
        return {
            'type': 'snowflake',
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.5, 1.8),
            'size': random.randint(5, 14),
            'shape_type': random.randint(0, 3),
            'angle': random.uniform(0, 360),
            'rot_speed': random.uniform(-0.7, 0.7),
            'base_alpha': base_alpha,
            'current_alpha': base_alpha
        }

    def create_petal(self, initial=False):
        base_alpha = random.randint(55, 110)
        return {
            'type': 'petal',
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.7, 1.8),
            'vx': 0.0, 'vy': 0.0,
            'sway_speed': random.uniform(0.015, 0.05),
            'sway_amp': random.uniform(15, 35),
            'offset_x': random.uniform(0, 100),
            'size': random.randint(12, 22),
            'shape_type': random.randint(0, 1),
            'angle': random.uniform(0, 360),
            'rot_speed': random.uniform(-1.0, 1.0),
            'alpha': base_alpha
        }

    def create_summer_leaf(self, initial=False):
        base_alpha = random.randint(60, 120)
        return {
            'type': 'summer_leaf',
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.8, 2.2),
            'sway_speed': random.uniform(0.02, 0.06),
            'sway_amp': random.uniform(20, 45),
            'offset_x': random.uniform(0, 100),
            'size': random.randint(14, 24),
            'angle': random.uniform(0, 360),
            'rot_speed': random.uniform(-1.0, 1.0),
            'alpha': base_alpha
        }

    def create_firefly(self, initial=False):
        return {
            'type': 'firefly',
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()),
            'base_x': random.randint(0, self.width()),
            'base_y': random.randint(0, self.height()),
            't': random.uniform(0, 100),
            't_speed': random.uniform(0.015, 0.035),
            'wave_x_amp': random.uniform(60, 150),
            'wave_y_amp': random.uniform(40, 100),
            'size': random.randint(8, 16),
            'alpha_offset': random.uniform(0, 10),
            'alpha_speed': 0.04,
            'flash_count': 0,
            'flash_timer': random.randint(80, 220)
        }

    def create_leaf(self, initial=False):
        base_alpha = random.randint(50, 95)
        color_type = random.choice(['maple_orange', 'maple_red', 'ginkgo_yellow'])
        return {
            'type': 'autumn_leaf',
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-40, -10),
            'speed': random.uniform(0.7, 2.0),
            'sway_speed': random.uniform(0.015, 0.05),
            'sway_amp': random.uniform(15, 40),
            'offset_x': random.uniform(0, 100),
            'size': random.randint(16, 26),
            'shape_type': random.randint(0, 2),
            'color_type': color_type,
            'angle': random.uniform(0, 360),
            'rot_speed': random.uniform(-1.2, 1.2),
            'alpha': base_alpha
        }

    def create_raindrop(self, initial=False):
        base_alpha = random.randint(70, 140)
        return {
            'type': 'raindrop',
            'x': random.randint(0, self.width()),
            'y': random.randint(0, self.height()) if initial else random.randint(-50, -10),
            'vy': random.uniform(1.5, 5.5),
            'size': random.randint(7, 13),
            'alpha': base_alpha,
            'mx_vx': 0.0, 'mx_vy': 0.0
        }

    def update_animation(self):
        cursor_global = QCursor.pos()
        cursor_local = self.mapFromGlobal(cursor_global)
        mx, my = cursor_local.x(), cursor_local.y()

        if self.current_theme == 'snow':
            for flake in self.particles:
                flake['y'] += flake['speed']
                dist = math.hypot(flake['x'] - mx, flake['y'] - my)
                if dist < 200:
                    flake['current_alpha'] += (0 - flake['current_alpha']) * 0.15
                else:
                    flake['current_alpha'] += (flake['base_alpha'] - flake['current_alpha']) * 0.08
                flake['angle'] += flake['rot_speed']
                if flake['y'] > self.height() + 30:
                    flake.update(self.create_snowflake(initial=False))

        elif self.current_theme == 'spring':
            for petal in self.particles:
                petal['y'] += petal['speed'] + petal['vy']
                petal['x'] += petal['vx']
                petal['offset_x'] += petal['sway_speed']
                petal['vx'] *= 0.85
                petal['vy'] *= 0.85
                current_x = petal['x'] + math.sin(petal['offset_x']) * petal['sway_amp']
                dist = math.hypot(current_x - mx, petal['y'] - my)
                if dist < 30 and dist > 0.1:
                    force = (1.0 - (dist / 30)) * 2.5
                    petal['vx'] += ((current_x - mx) / dist) * force
                    petal['vy'] += ((petal['y'] - my) / dist) * force + 0.1
                petal['angle'] += petal['rot_speed']
                if petal['y'] > self.height() + 30 or petal['x'] < -60 or petal['x'] > self.width() + 60:
                    petal.update(self.create_petal(initial=False))

        elif self.current_theme == 'summer_leaves':
            for p in self.particles:
                p['y'] += p['speed']
                p['offset_x'] += p['sway_speed']
                p['angle'] += p['rot_speed']
                if p['y'] > self.height() + 30:
                    p.update(self.create_summer_leaf(initial=False))

        elif self.current_theme == 'fireflies':
            for p in self.particles:
                p['t'] += p['t_speed']
                p['base_x'] += math.cos(p['t'] * 0.3) * 0.3
                p['base_y'] += math.sin(p['t'] * 0.2) * 0.3
                
                p['x'] = p['base_x'] + math.sin(p['t']) * p['wave_x_amp'] + math.cos(p['t'] * 0.5) * (p['wave_x_amp'] * 0.5)
                p['y'] = p['base_y'] + math.cos(p['t'] * 0.8) * p['wave_y_amp'] + math.sin(p['t'] * 0.4) * (p['wave_y_amp'] * 0.5)

                if p['base_x'] < -100: p['base_x'] = self.width() + 100
                elif p['base_x'] > self.width() + 100: p['base_x'] = -100
                if p['base_y'] < -100: p['base_y'] = self.height() + 100
                elif p['base_y'] > self.height() + 100: p['base_y'] = -100

                if p['flash_count'] > 0:
                    p['alpha_speed'] = 0.85
                    p['flash_count'] -= 1
                else:
                    p['flash_timer'] -= 1
                    if p['flash_timer'] <= 0:
                        p['flash_count'] = 15
                        p['flash_timer'] = random.randint(80, 220)
                    else:
                        p['alpha_speed'] = 0.04

                p['alpha_offset'] += p['alpha_speed']

        elif self.current_theme == 'autumn':
            for leaf in self.particles:
                leaf['y'] += leaf['speed']
                leaf['offset_x'] += leaf['sway_speed']
                leaf['angle'] += leaf['rot_speed']
                if leaf['y'] > self.height() + 30:
                    leaf.update(self.create_leaf(initial=False))

        elif self.current_theme == 'rain':
            for drop in self.particles:
                drop['y'] += drop['vy'] + drop['mx_vy']
                drop['x'] += drop['mx_vx']
                drop['mx_vx'] *= 0.85
                drop['mx_vy'] *= 0.85
                dist = math.hypot(drop['x'] - mx, drop['y'] - my)
                if dist < 30 and dist > 0.1:
                    force = (1.0 - (dist / 30)) * 2.5
                    drop['mx_vx'] += ((drop['x'] - mx) / dist) * force
                    drop['mx_vy'] += ((drop['y'] - my) / dist) * force + 0.1
                if drop['y'] > self.height() - 20:
                    if random.random() < 0.3:
                        self.ripples.append({
                            'x': drop['x'], 'y': random.randint(self.height() - 60, self.height() - 10),
                            'current_r': 2.0, 'max_r': random.randint(8, 15), 'alpha': random.randint(80, 140)
                        })
                    drop.update(self.create_raindrop(initial=False))

            for ripple in self.ripples[:]:
                ripple['current_r'] += 0.4
                ripple['alpha'] -= 4
                if ripple['alpha'] <= 0 or ripple['current_r'] >= ripple['max_r']:
                    self.ripples.remove(ripple)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.current_theme == 'snow':
            for flake in self.particles:
                alpha = int(flake['current_alpha'])
                if alpha < 3: continue
                painter.setPen(QPen(QColor(235, 245, 255, alpha), 0.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(Qt.NoBrush)
                painter.save()
                painter.translate(flake['x'], flake['y'])
                painter.rotate(flake['angle'])
                self.draw_snowflake(painter, flake['size'], flake['shape_type'])
                painter.restore()

        elif self.current_theme == 'spring':
            for petal in self.particles:
                alpha = int(petal['alpha'])
                if alpha < 3: continue
                painter.setPen(QPen(QColor(255, 140, 165, int(alpha * 1.2)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(255, 190, 205, int(alpha * 0.75))))
                cx = petal['x'] + math.sin(petal['offset_x']) * petal['sway_amp']
                painter.save()
                painter.translate(cx, petal['y'])
                painter.rotate(petal['angle'])
                self.draw_petal(painter, petal['size'], petal['shape_type'])
                painter.restore()

        elif self.current_theme == 'summer_leaves':
            for p in self.particles:
                alpha = int(p['alpha'])
                if alpha < 3: continue
                painter.setPen(QPen(QColor(60, 150, 90, int(alpha * 1.2)), 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(110, 210, 130, int(alpha * 0.7))))
                cx = p['x'] + math.sin(p['offset_x']) * p['sway_amp']
                painter.save()
                painter.translate(cx, p['y'])
                painter.rotate(p['angle'])
                self.draw_summer_leaf_shape(painter, p['size'])
                painter.restore()

        elif self.current_theme == 'fireflies':
            for p in self.particles:
                firefly_alpha = int((math.sin(p['alpha_offset']) + 1) * 75 + 15)
                gradient = QRadialGradient(QPointF(p['x'], p['y']), p['size'])
                gradient.setColorAt(0.0, QColor(255, 255, 150, firefly_alpha))
                gradient.setColorAt(0.4, QColor(210, 250, 60, int(firefly_alpha * 0.6)))
                gradient.setColorAt(1.0, QColor(120, 210, 30, 0))
                
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(gradient))
                painter.drawEllipse(QPointF(p['x'], p['y']), p['size'], p['size'])

        elif self.current_theme == 'autumn':
            for leaf in self.particles:
                alpha = int(leaf['alpha'])
                if alpha < 3: continue
                c_type = leaf['color_type']
                if c_type == 'maple_orange':
                    fill_c, pen_c = QColor(235, 130, 40, int(alpha * 0.7)), QColor(160, 75, 15, int(alpha * 1.2))
                elif c_type == 'maple_red':
                    fill_c, pen_c = QColor(215, 75, 45, int(alpha * 0.7)), QColor(140, 35, 15, int(alpha * 1.2))
                else:
                    fill_c, pen_c = QColor(250, 210, 50, int(alpha * 0.7)), QColor(175, 135, 15, int(alpha * 1.2))
                painter.setPen(QPen(pen_c, 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(fill_c))
                cx = leaf['x'] + math.sin(leaf['offset_x']) * leaf['sway_amp']
                painter.save()
                painter.translate(cx, leaf['y'])
                painter.rotate(leaf['angle'])
                self.draw_leaf(painter, leaf['size'], leaf['shape_type'])
                painter.restore()

        elif self.current_theme == 'rain':
            for drop in self.particles:
                alpha = int(drop['alpha'])
                if alpha < 3: continue
                painter.setPen(QPen(QColor(100, 175, 230, int(alpha * 1.2)), 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(190, 230, 250, int(alpha * 0.75))))
                painter.save()
                painter.translate(drop['x'], drop['y'])
                self.draw_water_drop(painter, drop['size'])
                painter.restore()

            for ripple in self.ripples:
                painter.setPen(QPen(QColor(170, 215, 245, max(0, ripple['alpha'])), 1.2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(ripple['x'], ripple['y']), ripple['current_r'], ripple['current_r'] * 0.35)

    def draw_snowflake(self, painter, size, shape_type):
        radius = size / 2.0
        if shape_type == 3:
            poly = QPolygonF([QPointF(radius*0.7*math.cos(j*math.pi/3), radius*0.7*math.sin(j*math.pi/3)) for j in range(6)])
            painter.drawPolygon(poly)
            return
        for i in range(6):
            painter.save()
            painter.rotate(i * 60)
            painter.drawLine(QPointF(0, 0), QPointF(0, -radius))
            painter.restore()

    def draw_petal(self, painter, size, shape_type):
        radius = size / 2.0
        if shape_type == 0:
            path = QPainterPath()
            path.moveTo(0, -radius)
            path.quadTo(radius * 0.7, -radius * 0.3, 0, radius)
            path.quadTo(-radius * 0.7, -radius * 0.3, 0, -radius)
            painter.drawPath(path)
            painter.fillPath(path, painter.brush())
        else:
            for i in range(5):
                painter.save()
                painter.rotate(i * 72)
                p_path = QPainterPath()
                p_path.addEllipse(QPointF(0, -radius * 0.5), radius * 0.35, radius * 0.5)
                painter.drawPath(p_path)
                painter.fillPath(p_path, painter.brush())
                painter.restore()

    def draw_summer_leaf_shape(self, painter, size):
        radius = size / 2.0
        path = QPainterPath()
        path.moveTo(0, radius)
        path.cubicTo(-radius * 0.7, radius * 0.4, -radius * 0.7, -radius * 0.7, 0, -radius)
        path.cubicTo(radius * 0.7, -radius * 0.7, radius * 0.7, radius * 0.4, 0, radius)
        path.closeSubpath()
        painter.drawPath(path)
        painter.fillPath(path, painter.brush())
        painter.setPen(QPen(painter.pen().color(), 1.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(0, radius * 0.8), QPointF(0, -radius * 0.6))

    def draw_leaf(self, painter, size, shape_type):
        radius = size / 2.0
        path = QPainterPath()
        if shape_type == 0:
            path.moveTo(0, -radius)
            path.quadTo(radius * 0.3, -radius * 0.5, radius * 0.9, -radius * 0.5)
            path.quadTo(radius * 0.4, 0, radius * 0.8, radius * 0.8)
            path.quadTo(0, radius * 0.4, -radius * 0.8, radius * 0.8)
            path.quadTo(-radius * 0.4, 0, -radius * 0.9, -radius * 0.5)
            path.closeSubpath()
        elif shape_type == 1:
            path.moveTo(0, radius * 0.85)
            path.cubicTo(-radius * 0.4, radius * 0.4, -radius * 1.8, -radius * 0.1, -radius * 2.1, -radius * 0.6)
            path.cubicTo(-radius * 1.4, -radius * 1.1, -radius * 0.4, -radius * 0.9, 0, -radius * 0.3)
            path.cubicTo(radius * 0.4, -radius * 0.9, radius * 1.4, -radius * 1.1, radius * 2.1, -radius * 0.6)
            path.cubicTo(radius * 1.8, -radius * 0.1, radius * 0.4, radius * 0.4, 0, radius * 0.85)
            path.closeSubpath()
        else:
            path.moveTo(0, radius)
            path.cubicTo(-radius * 0.8, radius * 0.5, -radius * 0.8, -radius * 0.8, 0, -radius)
            path.cubicTo(radius * 0.8, -radius * 0.8, radius * 0.8, radius * 0.5, 0, radius)
            path.closeSubpath()
        painter.drawPath(path)
        painter.fillPath(path, painter.brush())

    def draw_water_drop(self, painter, size, shape_type=0):
        radius = size / 2.0
        path = QPainterPath()
        path.moveTo(0, -radius)
        path.cubicTo(radius * 0.8, -radius * 0.2, radius * 0.9, radius * 0.9, 0, radius)
        path.cubicTo(-radius * 0.9, radius * 0.9, -radius * 0.8, -radius * 0.2, 0, -radius)
        path.closeSubpath()
        painter.drawPath(path)
        painter.fillPath(path, painter.brush())

    def quit_window(self):
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        self.root_app.quit()
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    shared_memory = QSharedMemory("DesktopSeasons_Unified_Key_2026")
    if not shared_memory.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("알림")
        msg.setText("LiveBg 위젯이 이미 실행 중입니다!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)

    widget = UnifiedSeasonsWidget()
    widget.root_app = app
    widget.show()
    sys.exit(app.exec_())