"""
result.dict.yaml 排序脚本
支持多种排序方式：按编码排序、按词组长度排序、按拼音排序等
"""

import os
import sys

def read_yaml_content(file_path):
    """读取 YAML 文件，分离头部、正文结构和可排序词条。"""
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在！")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    header = []
    body_items = []
    entries = []
    in_header = False
    has_header = False

    for line in lines:
        stripped = line.strip()
        # YAML 头部以 --- 开始，以 ... 结束
        if stripped == '---':
            in_header = True
            has_header = True
            header.append(line)
        elif stripped == '...' and has_header:
            header.append(line)
            in_header = False
        elif in_header:
            header.append(line)
        else:
            raw_line = line.rstrip('\n')
            if raw_line.lstrip().startswith('#'):
                body_items.append(('comment', raw_line))
            elif '\t' in raw_line:
                body_items.append(('entry', raw_line))
                entries.append(raw_line)
            else:
                body_items.append(('raw', raw_line))

    return header, body_items, entries

def sort_by_code(entries):
    """按编码排序（字母顺序）"""
    def get_code(entry):
        parts = entry.split('\t')
        return parts[1] if len(parts) > 1 else ''

    return sorted(entries, key=get_code)

def sort_by_word_length(entries):
    """按词组长度排序（从短到长）"""
    def get_word_length(entry):
        parts = entry.split('\t')
        word = parts[0] if len(parts) > 0 else ''
        return (len(word), entry)  # 先按长度，再按原始内容

    return sorted(entries, key=get_word_length)

def sort_by_code_length(entries):
    """按编码长度排序（从短到长）"""
    def get_code_length(entry):
        parts = entry.split('\t')
        code = parts[1] if len(parts) > 1 else ''
        return (len(code), code, entry)  # 先按编码长度，再按编码字母，最后按原始内容

    return sorted(entries, key=get_code_length)

def sort_by_word(entries):
    """按词组排序（拼音顺序）"""
    def get_word(entry):
        parts = entry.split('\t')
        return parts[0] if len(parts) > 0 else ''

    return sorted(entries, key=get_word)

def write_yaml_file(file_path, header, body_items, entries, backup=True):
    """写入排序后的 YAML 文件，同时保留注释与原始位置。"""
    # 备份原文件
    if backup and os.path.exists(file_path):
        backup_path = file_path + '.backup'
        import shutil
        shutil.copy(file_path, backup_path)
        print(f"已备份原文件到: {backup_path}")

    entry_iter = iter(entries)
    with open(file_path, 'w', encoding='utf-8') as f:
        # 写入头部
        f.writelines(header)
        # 写入正文，注释和其他非词条内容保持原位置
        for item_type, content in body_items:
            if item_type == 'entry':
                f.write(next(entry_iter) + '\n')
            else:
                f.write(content + '\n')

    print(f"排序完成！共处理 {len(entries)} 条词组")

def main():
    print("═══════════════════════════════════════")
    print("    result.dict.yaml 排序工具")
    print("═══════════════════════════════════════")
    print()

    file_path = './result.dict.yaml'

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：未找到 {file_path} 文件！")
        print("请确保该文件在当前目录下。")
        input("\n按任意键退出...")
        sys.exit(1)

    # 读取文件
    print("正在读取文件...")
    header, body_items, entries = read_yaml_content(file_path)
    print(f"读取成功！共 {len(entries)} 条词组")
    print()

    # 选择排序方式
    print("请选择排序方式：")
    print("1. 按编码排序（a-z 字母顺序）")
    print("2. 按词组长度排序（短→长）")
    print("3. 按编码长度排序（短→长）")
    print("4. 按词组排序（拼音顺序）")
    print("5. 退出")
    print()

    choice = input("请输入选项 (1-5): ").strip()

    if choice == '1':
        print("\n正在按编码排序...")
        sorted_entries = sort_by_code(entries)
    elif choice == '2':
        print("\n正在按词组长度排序...")
        sorted_entries = sort_by_word_length(entries)
    elif choice == '3':
        print("\n正在按编码长度排序...")
        sorted_entries = sort_by_code_length(entries)
    elif choice == '4':
        print("\n正在按词组排序...")
        sorted_entries = sort_by_word(entries)
    elif choice == '5':
        print("\n已取消操作。")
        return
    else:
        print("\n无效的选项！")
        input("\n按任意键退出...")
        return

    # 写入文件
    write_yaml_file(file_path, header, body_items, sorted_entries, backup=True)

    # 显示示例
    print("\n排序后的前 10 条示例：")
    for i, entry in enumerate(sorted_entries[:10], 1):
        print(f"  {i}. {entry}")

    print("\n完成！")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消。")
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按任意键退出...")
