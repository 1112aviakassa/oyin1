# -*- coding: utf-8 -*-
"""
Ilon o'yini (Snake Game) — Kivy, Android portrait.
Portal: devordan o'tib qarama-qarshi tomondan chiqadi (toroidal grid).
O'lim: faqat o'z tanasiga urilganda.
"""

from random import choice

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

# Ranglar
COLOR_BG = (0.07, 0.09, 0.14, 1)
COLOR_GRID = (0.12, 0.15, 0.22, 1)
COLOR_PORTAL = (0.2, 0.55, 0.75, 0.35)      # Devor portali belgisi
COLOR_PORTAL_FLASH = (0.35, 0.85, 1.0, 0.55)  # Portal orqali o'tganda
COLOR_SNAKE = (0.18, 0.85, 0.45, 1)
COLOR_SNAKE_HEAD = (0.25, 1.0, 0.55, 1)
COLOR_APPLE = (0.92, 0.22, 0.28, 1)
COLOR_SCORE = (0.9, 0.92, 0.95, 1)
COLOR_GAME_OVER = (1, 0.35, 0.35, 1)

BASE_TICK = 0.15
MIN_TICK = 0.07
CELL_MIN_DP = 18


def portal_step(coord: int, delta: int, size: int) -> tuple[int, bool]:
    """
    Eng to'g'ri portal formulasi (toroidal grid).

    (coord + delta) % size — Python'da manfiy indekslarni ham to'g'ri
    aylantiradi: masalan -1 % 14 == 13 (chapdan o'ngga o'tish).

    Qaytadi: (yangi_koordinata, portal_ishlatildimi)
    """
    raw = coord + delta
    wrapped = raw % size
    used_portal = raw < 0 or raw >= size
    return wrapped, used_portal


def portal_head(col: int, row: int, dx: int, dy: int, cols: int, rows: int):
    """Boshning keyingi katak joyi va portal holati."""
    new_col, wrap_x = portal_step(col, dx, cols)
    new_row, wrap_y = portal_step(row, dy, rows)
    return new_col, new_row, wrap_x or wrap_y


class GameBoard(Widget):
    """O'yin maydoni."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 14
        self.rows = 20
        self.cell_size = dp(20)
        self.offset_x = 0.0
        self.offset_y = 0.0

        self.snake: list[tuple[int, int]] = []
        self._body_set: set[tuple[int, int]] = set()
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.apple = (0, 0)
        self.score = 0
        self.game_over = False
        self.portal_flash = 0.0
        self._tick = BASE_TICK
        self._scheduled = False

        self.on_score_change = None
        self.on_game_over = None

        self.bind(size=self._on_resize, pos=self._on_resize)

    def _sync_body_set(self):
        self._body_set = set(self.snake)

    def _on_resize(self, *args):
        if self.width < 1 or self.height < 1:
            return

        cell_px = dp(CELL_MIN_DP)
        self.cols = max(10, int(self.width / cell_px))
        self.rows = max(14, int(self.height / cell_px))

        cell_w = self.width / self.cols
        cell_h = self.height / self.rows
        self.cell_size = min(cell_w, cell_h)

        grid_w = self.cell_size * self.cols
        grid_h = self.cell_size * self.rows
        self.offset_x = self.x + (self.width - grid_w) / 2
        self.offset_y = self.y + (self.height - grid_h) / 2
        self.redraw()

    def cell_to_pixel(self, col, row):
        x = self.offset_x + col * self.cell_size
        y = self.offset_y + (self.rows - 1 - row) * self.cell_size
        return x, y

    def _tick_for_score(self):
        """Ball oshganda biroz tezlashadi."""
        speedup = min(self.score * 0.004, BASE_TICK - MIN_TICK)
        return max(MIN_TICK, BASE_TICK - speedup)

    def reset_game(self):
        self.game_over = False
        self.score = 0
        self.portal_flash = 0.0
        self._tick = BASE_TICK
        self.direction = (1, 0)
        self.next_direction = (1, 0)

        mid_r = self.rows // 2
        mid_c = self.cols // 2
        self.snake = [
            (mid_c - 2, mid_r),
            (mid_c - 1, mid_r),
            (mid_c, mid_r),
        ]
        self._sync_body_set()
        self.spawn_apple()
        self.redraw()
        if self.on_score_change:
            self.on_score_change(self.score)

    def spawn_apple(self):
        occupied = self._body_set
        total = self.cols * self.rows
        if len(occupied) >= total:
            return
        while True:
            c = choice(range(self.cols))
            r = choice(range(self.rows))
            if (c, r) not in occupied:
                self.apple = (c, r)
                return

    def set_direction(self, dx, dy):
        if self.game_over:
            return
        # Navbatdagi yo'nalishga nisbatan 180° burilish bloklanadi
        ref = self.next_direction
        if (dx, dy) == (-ref[0], -ref[1]):
            return
        self.next_direction = (dx, dy)

    def start_loop(self):
        if not self._scheduled:
            self._scheduled = True
            Clock.schedule_interval(self.update, self._tick)

    def _reschedule_tick(self):
        if not self._scheduled:
            return
        Clock.unschedule(self.update)
        self._tick = self._tick_for_score()
        Clock.schedule_interval(self.update, self._tick)

    def stop_loop(self):
        if self._scheduled:
            Clock.unschedule(self.update)
            self._scheduled = False

    def update(self, dt):
        if self.game_over:
            return

        if self.portal_flash > 0:
            self.portal_flash = max(0.0, self.portal_flash - dt * 2.5)

        self.direction = self.next_direction
        dx, dy = self.direction
        head_c, head_r = self.snake[-1]

        new_c, new_r, used_portal = portal_head(
            head_c, head_r, dx, dy, self.cols, self.rows
        )
        new_head = (new_c, new_r)

        if used_portal:
            self.portal_flash = 1.0

        will_eat = new_head == self.apple
        # Dumaloq chiqsa bo'sh bo'ladi; yeyilsa dumaloq qoladi
        if will_eat:
            hit_body = new_head in self._body_set
        else:
            tail = self.snake[0]
            hit_body = new_head in self._body_set and new_head != tail

        if hit_body:
            self.game_over = True
            self.redraw()
            if self.on_game_over:
                self.on_game_over()
            return

        self.snake.append(new_head)
        self._body_set.add(new_head)

        if will_eat:
            self.score += 1
            if self.on_score_change:
                self.on_score_change(self.score)
            self.spawn_apple()
            self._reschedule_tick()
        else:
            tail = self.snake.pop(0)
            self._body_set.discard(tail)

        self.redraw()

    def redraw(self):
        self.canvas.clear()

        with self.canvas:
            Color(*COLOR_BG)
            Rectangle(pos=self.pos, size=self.size)

            if self.cell_size <= 0:
                return

            grid_w = self.cell_size * self.cols
            grid_h = self.cell_size * self.rows
            ox, oy = self.offset_x, self.offset_y

            # Portal devorlari (4 tomonda yengil chiziq)
            Color(*COLOR_PORTAL)
            t = max(2, self.cell_size * 0.06)
            Rectangle(pos=(ox, oy), size=(t, grid_h))                      # chap
            Rectangle(pos=(ox + grid_w - t, oy), size=(t, grid_h))         # o'ng
            Rectangle(pos=(ox, oy), size=(grid_w, t))                     # past
            Rectangle(pos=(ox, oy + grid_h - t), size=(grid_w, t))         # tepa

            Color(*COLOR_GRID)
            for c in range(self.cols + 1):
                x = ox + c * self.cell_size
                Rectangle(pos=(x, oy), size=(1, grid_h))
            for r in range(self.rows + 1):
                y = oy + r * self.cell_size
                Rectangle(pos=(ox, y), size=(grid_w, 1))

            pad_a = self.cell_size * 0.08
            ax, ay = self.cell_to_pixel(*self.apple)
            Color(*COLOR_APPLE)
            Ellipse(
                pos=(ax + pad_a, ay + pad_a),
                size=(self.cell_size - 2 * pad_a, self.cell_size - 2 * pad_a),
            )

            pad_s = self.cell_size * 0.06
            for i, (col, row) in enumerate(self.snake):
                x, y = self.cell_to_pixel(col, row)
                is_head = i == len(self.snake) - 1
                if is_head and self.portal_flash > 0:
                    Color(*COLOR_PORTAL_FLASH)
                    glow = self.cell_size * 0.02
                    RoundedRectangle(
                        pos=(x + pad_s - glow, y + pad_s - glow),
                        size=(
                            self.cell_size - 2 * pad_s + 2 * glow,
                            self.cell_size - 2 * pad_s + 2 * glow,
                        ),
                        radius=[dp(6)],
                    )
                Color(*(COLOR_SNAKE_HEAD if is_head else COLOR_SNAKE))
                RoundedRectangle(
                    pos=(x + pad_s, y + pad_s),
                    size=(self.cell_size - 2 * pad_s, self.cell_size - 2 * pad_s),
                    radius=[dp(4)],
                )


class SnakeApp(App):
    def build(self):
        Window.clearcolor = COLOR_BG
        if Window.width > Window.height:
            Window.size = (360, 640)

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        self.score_label = Label(
            text="Ball: 0",
            font_size=dp(22),
            bold=True,
            color=COLOR_SCORE,
            size_hint_y=None,
            height=dp(44),
        )
        root.add_widget(self.score_label)

        game_box = FloatLayout(size_hint=(1, 1))
        self.board = GameBoard(size_hint=(1, 1))
        self.board.on_score_change = self._update_score
        self.board.on_game_over = self._show_game_over
        game_box.add_widget(self.board)

        self.game_over_label = Label(
            text="O'yin tugadi",
            font_size=dp(28),
            bold=True,
            color=COLOR_GAME_OVER,
            opacity=0,
            halign="center",
            valign="middle",
        )
        self.game_over_label.bind(size=self.game_over_label.setter("text_size"))
        game_box.add_widget(self.game_over_label)
        root.add_widget(game_box)
        root.add_widget(self._build_dpad())

        Clock.schedule_once(lambda _: self._start(), 0.1)
        return root

    def _update_score(self, score):
        self.score_label.text = f"Ball: {score}"

    def _show_game_over(self):
        self.game_over_label.opacity = 1

    def _hide_game_over(self):
        self.game_over_label.opacity = 0

    def _start(self):
        self.board.reset_game()
        self._hide_game_over()
        self.board.start_loop()

    def _restart(self):
        self._hide_game_over()
        self.board.reset_game()
        if not self.board._scheduled:
            self.board.start_loop()

    def _pad_btn(self, text, dx, dy):
        btn = Button(
            text=text,
            font_size=dp(26),
            background_color=(0.22, 0.28, 0.38, 1),
            background_normal="",
            color=(1, 1, 1, 1),
        )
        btn.bind(on_press=lambda *_: self.board.set_direction(dx, dy))
        return btn

    def _build_dpad(self):
        pad = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(200),
            spacing=dp(6),
        )
        top = BoxLayout(size_hint_y=0.33, spacing=dp(6))
        top.add_widget(Widget())
        top.add_widget(self._pad_btn("▲", 0, 1))
        top.add_widget(Widget())

        mid = BoxLayout(size_hint_y=0.34, spacing=dp(6))
        mid.add_widget(self._pad_btn("◀", -1, 0))
        restart = Button(
            text="🔄",
            font_size=dp(28),
            background_color=(0.35, 0.45, 0.55, 1),
            background_normal="",
            color=(1, 1, 1, 1),
        )
        restart.bind(on_press=lambda *_: self._restart())
        mid.add_widget(restart)
        mid.add_widget(self._pad_btn("▶", 1, 0))

        bot = BoxLayout(size_hint_y=0.33, spacing=dp(6))
        bot.add_widget(Widget())
        bot.add_widget(self._pad_btn("▼", 0, -1))
        bot.add_widget(Widget())

        pad.add_widget(top)
        pad.add_widget(mid)
        pad.add_widget(bot)
        return pad

    def on_stop(self):
        self.board.stop_loop()


if __name__ == "__main__":
    SnakeApp().run()
