#!/usr/bin/env python3
"""반짝이는 별모양 슬랙 이모지 GIF 생성"""

import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import imageio.v3 as imageio
import numpy as np

SIZE = 128
CENTER = SIZE // 2
NUM_FRAMES = 20
FPS = 15

random.seed(42)

# 작은 반짝임(sparkle) 위치를 미리 생성
sparkle_positions = [(random.randint(10, 118), random.randint(10, 118)) for _ in range(12)]
sparkle_phases = [random.uniform(0, math.pi * 2) for _ in range(12)]

frames = []

for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    angle = t * 2 * math.pi

    # 짙은 남색 ~ 보라색 그라데이션 배경
    bg = Image.new("RGB", (SIZE, SIZE))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(SIZE):
        ratio = y / SIZE
        r = int(15 * (1 - ratio) + 40 * ratio)
        g = int(10 * (1 - ratio) + 15 * ratio)
        b = int(50 * (1 - ratio) + 80 * ratio)
        bg_draw.line([(0, y), (SIZE, y)], fill=(r, g, b))

    frame = bg.convert("RGBA")

    # 별 크기 펄스 (숨쉬는 효과)
    pulse = 1.0 + 0.12 * math.sin(angle)
    star_size = int(38 * pulse)

    # 별 뒤의 글로우 효과
    glow_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    glow_alpha1 = int(40 + 25 * math.sin(angle))
    glow_r1 = int(star_size * 1.8)
    glow_draw.ellipse(
        [CENTER - glow_r1, CENTER - glow_r1, CENTER + glow_r1, CENTER + glow_r1],
        fill=(255, 230, 100, glow_alpha1)
    )
    glow_alpha2 = int(60 + 30 * math.sin(angle + 0.5))
    glow_r2 = int(star_size * 1.3)
    glow_draw.ellipse(
        [CENTER - glow_r2, CENTER - glow_r2, CENTER + glow_r2, CENTER + glow_r2],
        fill=(255, 220, 80, glow_alpha2)
    )

    glow_blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=8))
    frame = Image.alpha_composite(frame, glow_blurred)

    # 메인 별 그리기
    star_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)

    rotation_offset = math.sin(angle) * 8
    points = []
    for i in range(10):
        a = (i * 36 - 90 + rotation_offset) * math.pi / 180
        radius = star_size if i % 2 == 0 else star_size * 0.4
        px = CENTER + radius * math.cos(a)
        py = CENTER + radius * math.sin(a)
        points.append((px, py))

    star_draw.polygon(points, fill=(255, 220, 50, 255), outline=(255, 180, 0, 255), width=2)

    # 별 내부 하이라이트
    inner_points = []
    for i in range(10):
        a = (i * 36 - 90 + rotation_offset) * math.pi / 180
        radius = (star_size * 0.6) if i % 2 == 0 else (star_size * 0.25)
        px = CENTER + radius * math.cos(a)
        py = CENTER + radius * math.sin(a)
        inner_points.append((px, py))
    star_draw.polygon(inner_points, fill=(255, 245, 150, 200))

    frame = Image.alpha_composite(frame, star_layer)

    # 반짝임(sparkle) 효과 - 십자 모양의 작은 빛들
    sparkle_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sparkle_draw = ImageDraw.Draw(sparkle_layer)

    for idx, (sx, sy) in enumerate(sparkle_positions):
        phase = sparkle_phases[idx]
        brightness = math.sin(angle * 2 + phase)
        if brightness > 0:
            alpha = int(brightness * 220)
            spark_size = int(brightness * 6) + 1
            color = (255, 255, 255, alpha)
            sparkle_draw.line([(sx - spark_size, sy), (sx + spark_size, sy)], fill=color, width=2)
            sparkle_draw.line([(sx, sy - spark_size), (sx, sy + spark_size)], fill=color, width=2)
            ds = max(1, spark_size // 2)
            sparkle_draw.line([(sx - ds, sy - ds), (sx + ds, sy + ds)], fill=(255, 255, 200, alpha // 2), width=1)
            sparkle_draw.line([(sx - ds, sy + ds), (sx + ds, sy - ds)], fill=(255, 255, 200, alpha // 2), width=1)

    frame = Image.alpha_composite(frame, sparkle_layer)

    # 별 꼭짓점에서 나오는 빛줄기
    ray_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ray_draw = ImageDraw.Draw(ray_layer)
    for i in range(5):
        a = (i * 72 - 90 + rotation_offset) * math.pi / 180
        ray_brightness = math.sin(angle * 3 + i * 1.2)
        if ray_brightness > 0.2:
            ray_alpha = int(ray_brightness * 100)
            ray_len = int(star_size * 1.4 + ray_brightness * 15)
            end_x = CENTER + ray_len * math.cos(a)
            end_y = CENTER + ray_len * math.sin(a)
            ray_draw.line(
                [(CENTER, CENTER), (end_x, end_y)],
                fill=(255, 255, 200, ray_alpha), width=2
            )

    frame = Image.alpha_composite(frame, ray_layer)

    # RGB로 변환
    frames.append(np.array(frame.convert("RGB")))

# GIF 저장
output_path = Path("/Users/damee/dev/my-first-skill/sparkling_star.gif")
frame_duration = 1000 / FPS

imageio.imwrite(
    output_path,
    frames,
    duration=frame_duration,
    loop=0,
)

file_size_kb = output_path.stat().st_size / 1024
print(f"GIF 생성 완료!")
print(f"  경로: {output_path}")
print(f"  크기: {file_size_kb:.1f} KB")
print(f"  해상도: {SIZE}x{SIZE}")
print(f"  프레임: {len(frames)}개 @ {FPS}fps")
print(f"  재생시간: {len(frames) / FPS:.1f}초")
