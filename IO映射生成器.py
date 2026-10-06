# -*- coding: utf-8 -*-
"""
IO 映射代码生成器
参照《IO映射工具.xlsx》的映射规则：
  I点：物理输入 -> 全局DB     "全局".变量名 := "变量名";
  Q点：全局DB -> 物理输出     "变量名" := "全局".变量名;

用法：
  运行脚本 -> 选择 IO 类型 -> 粘贴变量名（可多行/空格/逗号分隔，空行结束）
  -> 自动生成映射语句，打印 + 保存到 txt + 复制到剪贴板
"""

import os
import subprocess
import sys
from datetime import datetime

# 全局 DB 名称，可在启动时修改
GLOBAL_DB = "全局"

# 输出文件固定放在脚本/exe 同目录（不管从哪里启动都找得到）
# 注意：PyInstaller 打包后 __file__ 指向临时解压目录，必须用 sys.executable
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(_BASE_DIR, "IO映射输出.txt")


def ensure_output_file():
    """启动时就确保输出文件存在（没有就创建带说明的空文件），避免用户找不到"""
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"IO 映射输出（由 IO映射生成器.py 自动维护，{datetime.now().strftime('%Y-%m-%d')} 创建）\n"
                    "每次生成的映射语句会追加在下面，带时间戳和类型标记\n")


def copy_to_clipboard(text: str) -> bool:
    """把文本复制到 Windows 剪贴板（借助系统自带的 clip 命令）"""
    try:
        # clip 命令默认按 GBK/ANSI 处理，先编码转换避免中文乱码
        p = subprocess.run(
            ["clip"], input=text.encode("gbk", errors="replace"), check=True
        )
        return p.returncode == 0
    except Exception:
        return False


def parse_variables(raw: str) -> list:
    """
    解析用户输入的变量名：
    支持换行、空格、逗号、制表符混合分隔；自动去重（保持原顺序）
    """
    # 中文逗号也当作分隔符
    raw = raw.replace("，", ",").replace("\t", " ")
    tokens = []
    for seg in raw.replace(",", " ").replace("\n", " ").split(" "):
        name = seg.strip().strip('"')  # 去掉首尾空白和可能误粘贴的引号
        if name:
            tokens.append(name)
    # 去重，保持顺序
    seen = set()
    result = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def generate_mapping(io_type: str, names: list) -> str:
    """按 IO 类型生成映射语句"""
    lines = []
    if io_type == "I":
        # I点：物理输入 -> 全局DB
        for name in names:
            lines.append(f'"{GLOBAL_DB}".{name} := "{name}";')
    else:
        # Q点：全局DB -> 物理输出
        for name in names:
            lines.append(f'"{name}" := "{GLOBAL_DB}".{name};')
    return "\n".join(lines)


def main():
    global GLOBAL_DB
    # 控制台编码容错：遇到无法解码的字符不崩溃，避免打包后环境差异导致闪退
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    print("=" * 50)
    print("       IO 映射代码生成器（I点 / Q点）")
    # 启动时先确保输出文件存在，并告知位置
    ensure_output_file()
    print(f"输出文件：{OUTPUT_FILE}")
    print("=" * 50)

    # 全局 DB 名称设置
    db = input(f"全局DB名称（直接回车默认 [{GLOBAL_DB}]）：").strip()
    if db:
        GLOBAL_DB = db

    while True:
        print("\n" + "-" * 50)
        # 选择 IO 类型
        while True:
            t = input("选择 IO 类型：【1】I点（输入）  【2】Q点（输出） ：").strip()
            if t in ("1", "I", "i", "I点"):
                io_type = "I"
                break
            if t in ("2", "Q", "q", "Q点"):
                io_type = "Q"
                break
            print("  输入无效，请输 1 或 2")

        print(f"\n粘贴{io_type}点变量名（支持多行/空格/逗号分隔，输完双击回车结束）：")
        raw_lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            raw_lines.append(line)

        names = parse_variables("\n".join(raw_lines))
        if not names:
            print("  没有识别到任何变量名，重新开始")
            continue

        # 生成映射语句
        code = generate_mapping(io_type, names)

        # 打印结果
        print(f"\n>>> 生成 {len(names)} 条 {io_type}点映射：\n")
        print(code)

        # 追加保存到 txt（带时间戳和类型标记，方便积累）
        header = f"\n{'=' * 40}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}  {io_type}点 × {len(names)}\n{'=' * 40}\n"
        with open(OUTPUT_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(header + code + "\n")
        print(f"\n已追加保存到：{OUTPUT_FILE}")
        # 复制到剪贴板
        if copy_to_clipboard(code):
            print("已复制到剪贴板，直接去博途里 Ctrl+V 即可")
        else:
            print("（剪贴板复制失败，请手动从上方复制）")

        # 继续 or 退出
        again = input("\n继续生成下一批？（回车继续 / 输 q 退出）：").strip().lower()
        if again in ("q", "quit", "exit"):
            print("拜拜！")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已退出")
        sys.exit(0)
