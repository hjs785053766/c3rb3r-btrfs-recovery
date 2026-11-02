#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开工前环境自检：本地依赖、磁盘空间、配置文件。远端检查会打印成待执行命令。"""
import os, sys, json, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, 'config.json')
ok = True


def line(tag, msg, good):
    global ok
    if not good:
        ok = False
    print('[%s] %s' % ('OK ' if good else 'FAIL', msg))


print('=== C3RB3R 恢复工具箱 · 环境自检 ===\n')

# Python
line('py', 'Python %s' % sys.version.split()[0], sys.version_info >= (3, 8))

# Pillow
try:
    import PIL
    line('pil', 'Pillow %s' % PIL.__version__, True)
except Exception:
    line('pil', 'Pillow 未安装（图片校验需要）: pip install pillow', False)

# 配置
if not os.path.isfile(CFG):
    line('cfg', '缺少 config.json（请复制 config.example.json 并填写）', False)
    cfg = {}
else:
    cfg = json.load(open(CFG, encoding='utf-8'))
    line('cfg', 'config.json 已加载', True)
    for k in ('dev', 'share', 'out_root', 'work_dir', 'ffmpeg'):
        v = cfg.get(k, '')
        line('cfg', '%s = %s' % (k, v), bool(v) and '<' not in str(v))

# ffmpeg
ff = cfg.get('ffmpeg', '')
line('ffmpeg', 'ffmpeg 路径 %s' % ff, bool(ff) and os.path.isfile(ff))

# 磁盘
for d, need in (cfg.get('min_free_gb') or {}).items():
    try:
        free = shutil.disk_usage(d + ':\\').free / 1e9
        line('disk', '%s 剩余 %.0f GB（要求 ≥ %s GB）' % (d, free, need), free >= need)
    except Exception:
        line('disk', '%s 盘不可用' % d, False)

# 输出目录可写
out = cfg.get('out_root', '')
if out:
    try:
        os.makedirs(out, exist_ok=True)
        line('out', '输出目录可写: %s' % out, True)
    except Exception as e:
        line('out', '输出目录不可写: %s' % e, False)

print('\n--- 以下命令需要在源端（NAS）上执行并贴回结果 ---')
print('which btrfs btrfs-debug-tree btrfs-find-root btrfs-map-logical')
print('btrfs filesystem show %s' % cfg.get('dev', '<DEV>'))
print('lsattr -d %s/* | grep -c "C"' % cfg.get('share', '<SHARE>'))
print('python3 -V')
print('\n以上都通过后，按 AGENT_RUNBOOK.md 的阶段 0 开始。')
print('\n结果：%s' % ('全部通过' if ok else '存在未通过项，请先修复'))
sys.exit(0 if ok else 1)
