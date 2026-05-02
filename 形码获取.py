# 双拼词典处理脚本（最终版：彻底过滤配置头+制表符分隔+去重+Notepad4兼容）
import os
import csv

# ========== 配置项（仅需修改文件名即可） ==========
INPUT_FILE = "cat.danzi.dict.yaml"  # 你的源词典文件
OUTPUT_FILE = "jdx.csv"                # 输出文件，txt/csv/tsv都可以
ADD_HEADER = False                               # True=加表头，False=不加（和原文件格式一致）
# ====================================================

def main():
    # 校验源文件是否存在
    if not os.path.exists(INPUT_FILE):
        print(f"错误：找不到文件 {INPUT_FILE}，请确保脚本和词典文件放在同一文件夹")
        input("按回车键退出")
        return

    result = []
    seen = set()  # 去重专用，记录已出现的(汉字,第三位编码)组合
    skip_header = False

    # 读取并处理源文件
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped_line = line.strip()
        # 1. 跳过空行
        if not stripped_line:
            continue
        # 2. 核心：yaml头部跳过逻辑（处理---和...之间的所有配置行）
        if stripped_line == "---":
            skip_header = True
            continue
        if stripped_line == "...":
            skip_header = False
            continue
        if skip_header:
            continue
        # 3. 兜底过滤：直接过滤掉name/version/sort配置行，双重保险
        if stripped_line.startswith(("name:", "version:", "sort:")):
            continue
        # 4. 跳过注释行
        if stripped_line.startswith("#"):
            continue

        # 拆分汉字和编码，自动兼容原文件的制表符/空格分隔
        parts = stripped_line.split()
        if len(parts) < 2:
            continue
        
        hanzi = parts[0]       # 提取汉字
        code = parts[1]        # 提取编码
        
        # 核心规则：编码不足3位直接跳过，只取第3位字符
        if len(code) < 3:
            continue
        third_char = code[2]

        # 去重逻辑：完全相同的「汉字+第三位编码」只保留1条
        unique_key = (hanzi, third_char)
        if unique_key not in seen:
            seen.add(unique_key)
            result.append([hanzi, third_char])

    # 写入文件：制表符\t分隔，utf-8编码完美兼容Notepad4
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter='\t')
        # 按需写入表头
        if ADD_HEADER:
            writer.writerow(["汉字", "第三位编码"])
        # 写入最终处理后的内容
        writer.writerows(result)

    print(f"处理完成！")
    print(f"去重后最终保留行数：{len(result)} 行")
    print(f"文件已保存到：{OUTPUT_FILE}")
    input("按回车键退出")

if __name__ == "__main__":
    main()