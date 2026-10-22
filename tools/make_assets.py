#!/usr/bin/env python3
"""生成仓库配图：hero.png / social-preview.png / terminal.png（全部离线绘制）"""
import subprocess
from PIL import Image, ImageDraw, ImageFont

BOLD = "/usr/share/fonts/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/noto/NotoSansCJKSC-Regular.ttf"
MONO = "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc"   # Noto Sans Mono CJK，含等宽 + 中文

BG = (15, 23, 42)
CARD = (30, 41, 59)
LINE = (51, 65, 85)
TXT = (226, 232, 240)
DIM = (148, 163, 184)
BLUE = (96, 165, 250)
GREEN = (74, 222, 128)
AMBER = (251, 191, 36)


def f(path, size):
    return ImageFont.truetype(path, size)


def hero(w=1280, h=560, path="assets/hero.png"):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    # 背景网格点
    for x in range(0, w, 40):
        for y in range(0, h, 40):
            d.point((x, y), fill=(28, 38, 58))

    d.text((80, 96), "dsh-on-android", font=f(BOLD, 78), fill=TXT)
    d.text((84, 200), "DeepSeek Harness on Android", font=f(BOLD, 38), fill=BLUE)
    d.text((84, 254), "PRoot + Alpine  ·  musl / aarch64  ·  no root, no Chromium build",
           font=f(REG, 24), fill=DIM)

    chips = ["4 pitfalls solved", "node-pty musl build", "one-command install"]
    x = 84
    for c in chips:
        tw = d.textlength(c, font=f(REG, 20))
        d.rounded_rectangle([x, 318, x + tw + 34, 362], 22, fill=CARD, outline=LINE)
        d.text((x + 17, 329), c, font=f(REG, 20), fill=GREEN)
        x += tw + 50

    # 右侧手机 + 终端
    px, py, pw, ph = 900, 70, 250, 420
    d.rounded_rectangle([px, py, px + pw, py + ph], 26, fill=(17, 24, 39), outline=LINE, width=2)
    d.rounded_rectangle([px + 12, py + 40, px + pw - 12, py + ph - 30], 10, fill=(8, 12, 22))
    d.rounded_rectangle([px + pw // 2 - 26, py + 16, px + pw // 2 + 26, py + 26], 6, fill=LINE)
    mono = f(MONO, 15)
    lines = [("$ dsh-go", GREEN), ("启动中...", DIM), ("HTTP 200", TXT),
             ("127.0.0.1:3080", BLUE), ("", TXT), ("model:", DIM),
             ("DeepSeek-V4-Flash", TXT)]
    ty = py + 68
    for t, c in lines:
        d.text((px + 28, ty), t, font=mono, fill=c)
        ty += 26

    d.text((84, h - 62), "github.com/maple564/dsh-on-android", font=f(REG, 22), fill=LINE)
    img.save(path, optimize=True)
    print("wrote", path, img.size)


def social(w=1280, h=640, path="assets/social-preview.png"):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, w, 40):
        for y in range(0, h, 40):
            d.point((x, y), fill=(28, 38, 58))
    d.text((w // 2, 230), "dsh-on-android", font=f(BOLD, 86), fill=TXT, anchor="mm")
    d.text((w // 2, 318), "DeepSeek Harness 跑在 Android 手机上", font=f(BOLD, 40),
           fill=BLUE, anchor="mm")
    d.text((w // 2, 384), "PRoot + Alpine · musl/aarch64 · 四个坑的完整解法",
           font=f(REG, 26), fill=DIM, anchor="mm")
    d.text((w // 2, 470), "no root  ·  no Chromium  ·  sh install.sh && dsh-go",
           font=f(REG, 24), fill=GREEN, anchor="mm")
    img.save(path, optimize=True)
    print("wrote", path, img.size)


def terminal(path="assets/terminal.png"):
    # 真实抓取的输出
    def sh(c):
        p = subprocess.run(["sh", "-c", c], capture_output=True, text=True, timeout=60)
        return (p.stdout or p.stderr).strip()

    ver = sh("dsh --version")
    code = sh('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:3080/')
    pty = sh("""node -e "const pty=require('/opt/dsh-harness/node_modules/node-pty/lib/index.js');const p=pty.spawn('/bin/echo',['ok'],{});p.onExit(e=>{console.log('node-pty OK, exit='+e.exitCode);process.exit(0)})" """)
    node = sh("node -v")

    rows = [
        ("$ sh install.sh", GREEN),
        ("==> node %s / npm ready" % node, DIM),
        ("==> 重编译 node-pty（musl）", DIM),
        ("==> node-pty OK", DIM),
        ("==> 固化到 /opt/dsh-harness", DIM),
        ("==> 完成。验证： dsh --version", DIM),
        ("", TXT),
        ("$ dsh --version", GREEN),
        (ver, TXT),
        ("", TXT),
        (pty, TXT),
        ("", TXT),
        ("$ dsh-go", GREEN),
        ("启动中...", DIM),
        ("$ curl -w '%{http_code}' 127.0.0.1:3080/", GREEN),
        (code + "  ->  http://127.0.0.1:3080", BLUE),
    ]

    mono = f(MONO, 21)
    lh = 36
    w, h = 1080, 76 + lh * len(rows) + 20
    img = Image.new("RGB", (w, h), (8, 12, 22))
    d = ImageDraw.Draw(img)
    # 标题栏
    d.rounded_rectangle([0, 0, w - 1, h - 1], 14, fill=(8, 12, 22), outline=LINE, width=2)
    d.rounded_rectangle([0, 0, w, 48], 14, fill=(22, 30, 46))
    d.rectangle([0, 34, w, 48], fill=(22, 30, 46))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([22 + i * 26, 17, 22 + i * 26 + 14, 31], fill=c)
    d.text((w // 2, 24), "alpine ~ /opt/dsh-harness  (Android · aarch64 · musl)",
           font=f(REG, 17), fill=DIM, anchor="mm")

    y = 72
    for t, c in rows:
        if t:
            d.text((28, y), t, font=mono, fill=c)
        y += lh
    img.save(path, optimize=True)
    print("wrote", path, img.size)
    print("--- captured ---")
    for t, c in rows:
        if t:
            print(t)


if __name__ == "__main__":
    import sys, os
    os.makedirs("assets", exist_ok=True)
    hero()
    social()
    terminal()
