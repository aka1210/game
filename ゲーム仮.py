from tkinter import Tk, Canvas, SW
from dataclasses import dataclass, field
import random
import time

# =================================================
# 初期設定値(定数)
BOX_MARGIN = 50
BOX_TOP_X = BOX_MARGIN # ゲーム領域の左上X座標
BOX_TOP_Y = BOX_MARGIN # ゲーム領域の左上Y座標
BOX_WIDTH = 700        # ゲーム領域の幅
BOX_HEIGHT = 500       # ゲーム領域の高さ
BOX_CENTER = BOX_TOP_X + BOX_WIDTH / 2  # ゲーム領域の中心

CANVAS_WIDTH = BOX_TOP_X + BOX_WIDTH + BOX_MARGIN    # Canvasの幅
CANVAS_HEIGHT = BOX_TOP_Y + BOX_HEIGHT + BOX_MARGIN  # Canvasの高さ
CANVAS_BACKGROUND = "lightgray"                      # Canvasの背景色

DURATION = 0.01        # 描画間隔

NUM_COLS = 1                    # x方向のブロックの数
NUM_ROWS = 1                    # y方向のブロックの数
BLOCK_WIDTH = 80                # ブロックの幅
BLOCK_HEIGHT = 30               # ブロックの高さ
BLOCK_PAD = 5                   # ブロックの間(パディング)
BLOCK_TOP = 50                  # ブロックの上の隙間(回り込み用)
BLOCK_POINTS = 10               # ブロックの基礎点
BLOCK_SPAN_X = BLOCK_WIDTH + BLOCK_PAD
BLOCK_SPAN_Y = BLOCK_HEIGHT + BLOCK_PAD
BLOCK_COLORS = ["green", "blue", "darkgray","pink","red","yellow"]  # ブロックの色

SPEED_UP = 5  # ボールを加速させる頻度
BLOCK_FALL_SPEED = 1  # ブロックが落ちる初速を遅くする
BLOCK_FALL_ACCELERATION = 0.001  # ブロックの落ちる速度の加速

PADDLE_WIDTH = 100  # パドルの幅
PADDLE_HEIGHT = 20  # パドルの高さ
PADDLE_X0 = BOX_TOP_X + (BOX_WIDTH - PADDLE_WIDTH) / 2  # パドルの初期位置(x)
PADDLE_Y0 = BOX_TOP_Y + BOX_HEIGHT - 60  # パドルの初期位置(y)
PADDLE_COLORS = ["blue", "red", "green", "yellow", "brown", "gray"]  # 変える色を用意する。

PADDLE_VX = 10  # パドルの移動速度を追加

# ----------------------------------
# 共通の親クラスとして、MovingObjectを定義
@dataclass
class MovingObject:
    id: int
    x: int
    y: int
    w: int
    h: int
    vx: int
    vy: int

    def redraw(self):  # 再描画(移動結果の画面反映)
        canvas.coords(self.id, self.x, self.y, self.x + self.w, self.y + self.h)

    def move(self):  # 移動させる
        self.x += self.vx
        self.y += self.vy


# Paddleは、MovingObjectを継承している。
class Paddle(MovingObject):
    def __init__(self, id, x, y, w, h, c):
        MovingObject.__init__(self, id, x, y, w, h, 0, 0)
        self.c = c

    def set_v(self, v):
        self.vx = v  # 移動量の設定は、独自メソッド

    def stop(self):  # 停止も、Paddle独自のメソッド
        self.vx = 0


# ブロック
@dataclass
class Block:
    id: int
    x: int
    y: int
    w: int
    h: int
    pt: int
    bc: int
    c: str


# ----------------------------------
# Box(ゲーム領域)の定義
@dataclass
class Box:
    west: int
    north: int
    east: int
    south: int
    paddle: Paddle
    paddle_v: int
    block: Block
    duration: float
    run: int
    score: int

    def __init__(self, x, y, w, h, duration):
        self.west, self.north = (x, y)
        self.east, self.south = (x + w, y + h)
        self.paddle = None
        self.block = None
        self.paddle_v = PADDLE_VX
        self.duration = duration
        self.run = False
        self.score = 0  # 得点

    # 壁の生成
    def make_walls(self):
        canvas.create_rectangle(self.west, self.north, self.east, self.south, outline="black")

    # パドルの生成
    def create_paddle(self, x, y, w, h, c):
        id = canvas.create_rectangle(x, y, x + w, y + h, fill=c)
        return Paddle(id, x, y, w, h, c)

    def create_block(self, x, y, w, h, pt, bc, c):  # ブロックの生成
        id = canvas.create_rectangle(x, y, x + w, y + h, fill=c)
        return Block(id, x, y, w, h, pt, bc, c)

    def check_block(self, block, paddle):  # ブロックがパドルに当たったか判定
        if (block.y + block.h >= paddle.y and block.x + block.w >= paddle.x
                and block.x <= paddle.x + paddle.w):
            return True
        return False

    def left_paddle(self, event):  # パドルを左に移動(Event処理)
        self.paddle.set_v(- self.paddle_v)

    def right_paddle(self, event):  # パドルを右に移動(Event処理)
        self.paddle.set_v(self.paddle_v)

    def stop_paddle(self, event):  # パドルを止める(Event処理)
        self.paddle.stop()

    def game_start(self, event):
        self.run = True

    def game_end(self, message):
        self.run = False
        canvas.create_text(BOX_CENTER, BOX_HEIGHT / 2, text=message, font=('FixedSys', 16))
        tk.update()

    def update_score(self):
        canvas.itemconfigure(self.id_score, text="score:" + str(self.score))

    def wait_start(self):
        # SPACEの入力待ち
        id_text = canvas.create_text(BOX_CENTER, BOX_HEIGHT / 2, text="Press 'SPACE' to start",
                                     font=('FixedSys', 16))
        tk.update()
        while not self.run:  # ひたすらSPACEを待つ
            tk.update()
            time.sleep(self.duration)
        canvas.delete(id_text)  # SPACE入力のメッセージを削除
        tk.update()

    def set(self):  # 初期設定を一括して行う
        # 壁の描画
        self.make_walls()
        # スコアの表示
        self.id_score = canvas.create_text(
            BOX_TOP_X,
            BOX_TOP_Y - 2,
            text=("score: " + str(self.score)),
            font=("FixedSys", 16), justify="left",
            anchor=SW
        )
        # パドルの生成
        self.paddle = self.create_paddle(PADDLE_X0, PADDLE_Y0, PADDLE_WIDTH, PADDLE_HEIGHT,
                                         random.choice(PADDLE_COLORS))
        # ブロックの生成
        self.block = self.create_block(
            random.randint(self.west, self.east - BLOCK_WIDTH),
            self.north + BLOCK_TOP,
            BLOCK_WIDTH, BLOCK_HEIGHT,
            BLOCK_POINTS, 1,
            random.choice(BLOCK_COLORS)
        )
        # イベント処理の登録
        canvas.bind_all('<KeyPress-Right>', self.right_paddle)
        canvas.bind_all('<KeyPress-Left>', self.left_paddle)
        canvas.bind_all('<KeyRelease-Right>', self.stop_paddle)
        canvas.bind_all('<KeyRelease-Left>', self.stop_paddle)
        canvas.bind_all('<KeyPress-space>', self.game_start)  # SPACEが押された

    def animate(self):
        block_fall_speed = BLOCK_FALL_SPEED
        while self.run:
            # ブロックの移動
            self.block.y += block_fall_speed
            canvas.coords(self.block.id, self.block.x, self.block.y, self.block.x + self.block.w,
                          self.block.y + self.block.h)
            if self.check_block(self.block, self.paddle):
                self.score += self.block.pt
                self.update_score()
                canvas.delete(self.block.id)
                self.block = self.create_block(
                    random.randint(self.west, self.east - BLOCK_WIDTH),
                    self.north + BLOCK_TOP,
                    BLOCK_WIDTH, BLOCK_HEIGHT,
                    BLOCK_POINTS, 1,
                    random.choice(BLOCK_COLORS)
                )

            # ゲームオーバー判定
            if self.block.y + self.block.h >= self.south:
                if self.score>=500:
                    self.game_end("Excellent!!")
                elif self.score>=300 and self.score<500:
                    self.game_end("Good!")
                elif self.score<300:
                    self.game_end("Game Over..")
                    break

            # パドルの移動
            self.paddle.move()
            if self.paddle.x < self.west:  # 左の壁にめり込んだ場合
                self.paddle.x = self.west
            elif self.paddle.x + self.paddle.w > self.east:  # 右の壁にめり込んだ場合
                self.paddle.x = self.east - self.paddle.w
            self.paddle.redraw()

            tk.update()
            time.sleep(self.duration)
            block_fall_speed += BLOCK_FALL_ACCELERATION


# =================================================
# 動作部分

tk = Tk()
tk.title("Falling Block Game")  # タイトルを付けてみました。

canvas = Canvas(tk, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=CANVAS_BACKGROUND)
canvas.pack()

# ゲームのインスタンスを作成し、初期設定を行う。
game = Box(BOX_TOP_X, BOX_TOP_Y, BOX_WIDTH, BOX_HEIGHT, DURATION)
game.set()

# ゲーム開始のための待機
game.wait_start()

# ゲームのメインループ
game.animate()

tk.mainloop()
