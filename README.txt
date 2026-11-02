C3RB3R（.L0CK3D）btrfs 数据恢复工具箱
================================================

本工具箱来自一次真实事故的完整复盘：206,000 个加密文件 / 1,033 GB，
最终在无密钥条件下恢复 125,405 个文件 / 573 GB（照片视频原图约 98%）。

配套文档：C3RB3R_btrfs_数据恢复手册.docx（先读它，里面是原理和完整流程）
交给 AI 执行：AGENT_RUNBOOK.md（面向 Agent 的分阶段作业指导，含成功判据与失败分支）
配置文件：config.example.json（复制成 config.json 后填写）
环境自检：python selfcheck.py

------------------------------------------------
目录结构
------------------------------------------------
nas_scripts/     在 NAS 上运行的只读脚本（用 sudo python3 执行）
local_drivers/   在操作机（Windows）上运行的驱动脚本
tools_windows/   Windows 专用小工具（askpass.exe）
C3RB3R_btrfs_数据恢复手册.docx

------------------------------------------------
依赖
------------------------------------------------
NAS 端：btrfs-progs（btrfs-debug-tree / btrfs-find-root / btrfs-map-logical）
        Python 3.8+
操作机：Python 3.8+、Pillow、ffmpeg、OpenSSH 客户端
        Windows 上还需要 askpass.exe（见下）

------------------------------------------------
快速开始（详细参数见手册第 5 章）
------------------------------------------------
0) 只读原则：不要对源盘做任何写操作，不要 balance / scrub / defrag。

1) 普查
   python nas_scripts/census_photos.py /volume1/homes/<user>/Photos
   python nas_scripts/census_sizes.py <base64(目录)>

2) A 类（0x25/0x26，照片视频原图）—— 收益最高，先做
   python local_drivers/run_local_fast.py <远端目录> <本地输出根> fail_A.tsv

3) 旧根 bookend（补 A 类失败）
   btrfs-find-root -a /dev/mapper/<设备> > findroot.txt
   python nas_scripts/resolve262.py <root_tree_block...>
   python local_drivers/run_bookend.py 清单.txt <输出根> prog.txt fail.tsv /volume1/homes/<user>/Photos/

4) B 类（>128 MiB 大视频）
   python local_drivers/run_big_multi.py <远端目录> <输出根> fail_B.tsv 0 prog.txt <分片k> <分片n>

5) C 类（0x24 小文件，空闲空间雕刻）
   btrfs-debug-tree -t 10 <设备> > free_tree.txt
   python nas_scripts/parse_free_space.py free_tree.txt free.json
   python nas_scripts/make_ranges.py free.json ranges.txt
   ssh <host> "sudo python3 /tmp/raw_reader2.py" > free.bin     （镜像放 SSD！）
   python nas_scripts/carve_c.py
   python nas_scripts/match_c.py

------------------------------------------------
使用前必须修改的路径
------------------------------------------------
脚本里有些路径是作者本机的，直接跑会失败，先全局搜一下改掉：
  - 设备路径      DEV = '/dev/mapper/cachedev_0'
  - 落地根目录    <OUT> / F:\恢复数据_xxx
  - 失败清单路径  *.tsv / *.csv
  - ffmpeg 路径   FFMPEG = r'E:\剪映\...\ffmpeg.exe'

------------------------------------------------
Windows 的 askpass
------------------------------------------------
Windows OpenSSH 不接受命令行传密码。用法：
  1. askpass.exe 放在纯 ASCII 路径（如 %TEMP%），不能放中文目录；
  2. 设环境变量 SSH_ASKPASS=<路径>、SSH_ASKPASS_REQUIRE=force、DISPLAY=localhost:0；
  3. 密码通过 askpass 程序返回（源码就是一个读取 stdin 的极简 C# 程序）。

------------------------------------------------
注意事项
------------------------------------------------
- 全过程只读源盘；恢复产物写到另一块盘。
- 每个恢复出来的文件都要做完整解码校验（ffmpeg / Pillow），校验不过的不算成功。
- 失败清单从磁盘反查生成，不要用日志行数（并行重试会产生重复行）。
- 本工具仅用于自己有权处理的数据恢复与取证。
