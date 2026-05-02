# 词典词条精准替换脚本（严格行首完整匹配+制表符校验，零误触）
import os

# ========== 配置项（和你的文件名完全匹配，不用改直接用） ==========
DICT_FILE = "result.dict.yaml"       # 你的源词典文件
REPLACE_RULE_FILE = "result.txt"     # 你写好对应关系的txt规则文件
OUTPUT_FILE = "替换完成.dict.yaml"  # 生成的新文件，不覆盖原文件
# ======================================================================

def main():
    # 校验文件是否存在
    for file_path in [DICT_FILE, REPLACE_RULE_FILE]:
        if not os.path.exists(file_path):
            print(f"错误：找不到文件【{file_path}】，请把脚本和两个文件放在同一个文件夹")
            input("按回车键退出")
            return

    # 1. 读取替换规则：原词=key，目标内容=value（无视目标内容里的所有符号，全保留）
    replace_map = {}
    with open(REPLACE_RULE_FILE, "r", encoding="utf-8") as f:
        rule_lines = f.readlines()

    for line_num, line in enumerate(rule_lines, 1):
        line_stripped = line.strip()
        # 跳过空行
        if not line_stripped:
            continue
        # 只按制表符拆分，拆成【原词】和【完整目标内容】，只拆第一个制表符
        if "\t" not in line:
            print(f"警告：第{line_num}行无制表符分隔，已跳过 | 内容：{line_stripped}")
            continue
        key, value = line.split("\t", 1)
        # 去首尾空格，存入对应关系
        key = key.strip()
        value = value.strip()
        if not key:
            print(f"警告：第{line_num}行原词为空，已跳过")
            continue
        replace_map[key] = value

    if not replace_map:
        print("错误：没有读取到任何有效的替换规则，请检查result.txt的格式")
        input("按回车键退出")
        return
    print(f"✅ 成功读取 {len(replace_map)} 条替换规则")

    # 2. 逐行处理词典文件，严格行首+制表符匹配替换
    final_content = []
    replaced_count = 0

    with open(DICT_FILE, "r", encoding="utf-8") as f:
        dict_lines = f.readlines()

    for line in dict_lines:
        line_stripped = line.strip()
        # 空行、yaml头部、配置行、注释行，全部原样保留，不做任何修改
        if (
            not line_stripped
            or line_stripped in ["---", "..."]
            or line_stripped.startswith(("#", "name:", "version:", "sort:"))
        ):
            final_content.append(line.rstrip("\n"))
            continue

        # 核心匹配逻辑：严格校验「行首完整原词 + 紧跟制表符」
        matched = False
        for original_word, target_word in replace_map.items():
            # 唯一匹配条件：这一行的开头，必须是【完整原词+制表符】
            match_flag = f"{original_word}\t"
            if line.startswith(match_flag):
                # 只替换行首的原词，后面的制表符、编码、所有内容全部原样保留
                new_line = line.replace(original_word, target_word, 1)
                final_content.append(new_line.rstrip("\n"))
                replaced_count += 1
                print(f"🔄 替换成功：【{original_word}】 → 【{target_word}】")
                matched = True
                break  # 匹配到就停止，避免重复替换
        # 没匹配到的行，原样保留
        if not matched:
            final_content.append(line.rstrip("\n"))

    # 3. 写入最终的新文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(final_content))

    # 4. 结果提示
    print(f"\n===== 处理完成 =====")
    print(f"✅ 共成功替换 {replaced_count} 条词条")
    print(f"✅ 新文件已生成：【{OUTPUT_FILE}】")
    print(f"✅ 原词典文件未做任何修改，可放心使用")
    input("按回车键退出")

if __name__ == "__main__":
    main()