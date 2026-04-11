# All.txt，存放需要转换的词组，每行一词，支持两种格式：
#   1. 纯词组：每行一个词组
#   2. 词组+编码：词组\t编码（只提取词组部分）
# jdx.csv，单字的首笔形码，用的 RIME_JD 的单字码表
# jdAllx.csv，最后得到的键道音形码文件

# 导入需要的模块
import glob
import re, csv, os
from itertools import product
from pypinyin import lazy_pinyin, Style

print('正在处理，请稍等……（参考： 平均1万词大约10秒时间，转化完成后，窗口会自动关闭）')

# 判断文件是否存在
file_list = ['jdAll.csv', 'jdAllx.csv', 'jdf.csv', 'jdy.csv', 'jdyf.csv', 'pinyin.csv', '已有字词.txt', '已有编码.txt', 'result.dict.yaml', '未匹配音节.txt']
for file in file_list:
    if os.path.exists(file):
        os.remove(file)

# 把词组存储到 Alltxt 列表中，支持"词组"或"词组\t编码"两种格式
# 只忽略文件最开头第一条注释，后续 # 注释行会原样保留到输出结果中。
with open('./All.txt', 'r', encoding='UTF-8-SIG') as f:
    Alltxt = []
    skipped_leading_comment = False
    for line in f:
        line = line.rstrip().lstrip('\ufeff')
        if not line:  # 跳过空行
            continue
        if line.lstrip().startswith('#'):
            if not skipped_leading_comment:
                skipped_leading_comment = True
                continue
            Alltxt.append(line)
            continue
        # 如果包含制表符，只取第一部分（词组）
        if '\t' in line:
            word = line.split('\t')[0]
            Alltxt.append(word)
        else:
            Alltxt.append(line)
# 使用 py2jd.txt 和自定义注音表统一生成拼音与键道音码

def process_row_to_code(row):
    """将 CSV 行转换为编码"""
    if len(row) == 3:  # 二字词
        try:
            sy1 = row[1][:2]
            sy2 = row[2][:2]
            return sy1+sy2
        except:
            return None
    elif len(row) == 4:  # 三字词
        try:
            s1 = row[1][:1]
            s2 = row[2][:1]
            s3 = row[3][:1]
            return s1+s2+s3
        except:
            return None
    elif len(row) == 5:  # 四字词
        try:
            s1 = row[1][:1]
            s2 = row[2][:1]
            s3 = row[3][:1]
            s4 = row[4][:1]
            return s1+s2+s3+s4
        except:
            return None
    elif len(row) > 5:  # 五字及以上词
        try:
            s1 = row[1][:1]
            s2 = row[2][:1]
            s3 = row[3][:1]
            s4 = row[-1][:1]  # 最后一个字
            return s1+s2+s3+s4
        except:
            return None
    return None

def load_py2jd_map(path):
    """读取拼音到键道编码的映射表，支持同一拼音对应多条编码。"""
    py2jd_map = {}
    with open(path, 'r', encoding='UTF-8') as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text or text.startswith('#'):
                continue

            parts = text.split()
            if len(parts) != 2:
                print(f'忽略 py2jd.txt 第{line_no}行：格式错误')
                continue

            pinyin, code = parts[0].lower(), parts[1].lower()
            py2jd_map.setdefault(pinyin, [])
            if code not in py2jd_map[pinyin]:
                py2jd_map[pinyin].append(code)

    return py2jd_map

def load_custom_pinyin(path):
    """读取自定义注音表，格式为：词组<Tab>拼音。"""
    custom_map = {}
    if not os.path.exists(path):
        return custom_map

    with open(path, 'r', encoding='UTF-8-SIG') as f:
        for line_no, line in enumerate(f, start=1):
            text = line.rstrip('\n')
            if not text.strip() or text.lstrip().startswith('#'):
                continue

            parts = text.split('\t', 1)
            if len(parts) != 2:
                print(f'忽略 custom_pinyin.txt 第{line_no}行：请使用 Tab 分隔')
                continue

            word = parts[0].strip()
            syllables = [item.strip().lower() for item in parts[1].split() if item.strip()]
            if not word or not syllables:
                print(f'忽略 custom_pinyin.txt 第{line_no}行：词组或拼音为空')
                continue

            custom_map[word] = syllables

    return custom_map

def get_word_pinyin(word, custom_map):
    """优先使用自定义注音，其次回退到 pypinyin 默认注音。"""
    custom_syllables = custom_map.get(word)
    if custom_syllables:
        if len(custom_syllables) == len(word):
            return custom_syllables, 'custom'
        print(f'custom_pinyin.txt 中“{word}”音节数量与字数不符，改用默认注音')

    syllables = lazy_pinyin(word, style=Style.NORMAL, strict=False, errors='ignore')
    syllables = [item.lower() for item in syllables if item]
    return syllables, 'pypinyin'

def expand_word_codes(word, syllables, py2jd_map):
    """把一个词的拼音列表展开为所有可能的键道编码。"""
    code_groups = []
    missing = []

    for syllable in syllables:
        codes = py2jd_map.get(syllable)
        if not codes:
            missing.append(syllable)
            continue
        code_groups.append(codes)

    if missing:
        return [], missing

    word_codes = []
    seen = set()
    for combo in product(*code_groups):
        code = process_row_to_code([word] + list(combo))
        if code and code not in seen:
            seen.add(code)
            word_codes.append(code)

    return word_codes, []

py2jd_map = load_py2jd_map('py2jd.txt')
custom_pinyin_map = load_custom_pinyin('custom_pinyin.txt')
missing_entries = []

# 统一生成注音结果和音码结果，键道规则完全以 py2jd.txt 为准。
with open('pinyin.csv', 'w', encoding='UTF-8-sig') as pinyin_file, open('jdAll.csv', 'w', encoding='UTF-8-sig') as jda:
    for word in Alltxt:
        if not word:
            continue
        if word.lstrip().startswith('#'):
            pinyin_file.write(word + '\n')
            jda.write(word + '\n')
            continue

        syllables, source = get_word_pinyin(word, custom_pinyin_map)
        if len(syllables) != len(word):
            missing_entries.append(f'{word}\t注音数量与字数不符\t{" ".join(syllables)}')
            continue

        pinyin_file.write(word + '\t' + '\t'.join(syllables) + '\n')

        word_codes, missing = expand_word_codes(word, syllables, py2jd_map)
        if missing:
            missing_entries.append(f'{word}\t缺少拼音映射\t{" ".join(missing)}\t来源:{source}')
            continue

        for code in word_codes:
            jda.write(f"{word}\t{code}\n")

if missing_entries:
    with open('未匹配音节.txt', 'w', encoding='UTF-8-sig') as f:
        for entry in missing_entries:
            f.write(entry + '\n')

# 去除重复编码，保留多编码词条
# 使用手动去重保持 All.txt 的原始顺序
seen_entries = set()  # 用于去重
result_lines = []

with open('jdAll.csv', 'r', encoding='UTF-8-sig') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            result_lines.append(line + '\n')
            continue

        parts = line.split('\t')
        if len(parts) != 2:
            continue

        word = parts[0].replace('\ufeff', '').strip()
        code = parts[1].strip()

        key = f"{word}_{code}"
        if key not in seen_entries:
            seen_entries.add(key)
            result_lines.append(f"{word}\t{code}\n")
# 写回文件，保持原始顺序
with open('jdAll.csv', 'w', encoding='UTF-8-sig') as f:
    f.writelines(result_lines)

# 将首笔对应码转为字典
dictx = {}
with open('jdx.csv', 'r+', encoding='UTF-8') as f:
    reader=csv.reader(f, dialect=csv.excel_tab)
    for row in reader:
        dictx[row[0]]=row[1]

# 开始添加形码，最核心、最常用的词库可以不加形码以降低码长
# 把音码存为列表
with open('jdAll.csv', 'r', encoding='UTF-8-sig') as file:
    datax = file.readlines()

# 添加形码
with open('jdAllx.csv', 'w', encoding='UTF-8') as jdAllx:
    for cizu in datax:
        # 保留注释行
        if cizu.lstrip().startswith('#'):
            jdAllx.write(cizu)
            continue

        # 分割词组和编码
        parts = cizu.strip().split('\t')
        if len(parts) != 2:
            continue

        word, code = parts[0], parts[1]

        # 三字词：添加3个形码
        if len(word) == 3:
            try:
                x1 = dictx[word[0]]
                x2 = dictx[word[1]]
                x3 = dictx[word[2]]
                jdAllx.write(f"{word}\t{code}{x1}{x2}{x3}\n")
            except Exception as e:
                # 字不在形码表中，跳过
                pass
        # 二字词或其他：添加2个形码
        else:
            try:
                x1 = dictx[word[0]]
                x2 = dictx[word[1]]
                jdAllx.write(f"{word}\t{code}{x1}{x2}\n")
            except Exception as e:
                # 字不在形码表中，跳过
                pass

#####################
### Added by Ivan ###
#####################

pattern = r'^.*\t[a-z]*'
output_zc_file = "./已有字词.txt"
output_bm_file = "./已有编码.txt"

# 1. 获取已有的编码和字词
file_list = [output_zc_file, output_bm_file]
for file in file_list:
    if os.path.exists(file):
        os.remove(file)

# 打开输出文件
with open(output_bm_file, 'w', encoding='utf-8') as outfile_bm, open(output_zc_file, 'w', encoding='utf-8') as outfile_zc:
    # 遍历目录下的所有yaml文件
    for filename in glob.glob('./*.dict.yaml'):
        # 打开yaml文件
        with open(filename, 'r', encoding='utf-8') as infile:
            # 读取yaml文件中的所有行
            lines = infile.readlines()

            # 标记是否在需要跳过的 region 内部
            in_skip_region = False
            separator_found = False

            for line in lines:
                # 检测到 ... 分隔符
                if line.strip() == '...':
                    separator_found = True
                    continue

                # 只处理 ... 之后的内容
                if not separator_found:
                    continue

                # 检测需要跳过的 #region（简字、简码等）
                # 只跳过包含"简"字的 region
                if line.strip().startswith('#region') and '简' in line:
                    in_skip_region = True
                    continue

                # 检测 #endregion 结束
                if line.strip().startswith('#endregion') and in_skip_region:
                    in_skip_region = False
                    continue

                # 在需要跳过的 region 内部，跳过
                if in_skip_region:
                    continue

                # 跳过普通注释行和 region 标记行
                if line.strip().startswith('#'):
                    continue

                # 匹配正则表达式，将匹配结果写入输出文件
                if re.search(pattern, line):
                    outfile_bm.write(line.split("\t")[1])      # 编码文件写入编码
                    outfile_zc.write(line.split("\t")[0]+"\n") # 字词文件写入字词

# 2. 读取 已有编码.txt 文件中的内容，存储在集合中
with open(output_bm_file, 'r', encoding='utf-8') as f:
    bm_set = set(line.strip() for line in f)

# 3. 读取 已有字词.txt 文件中的内容，存储在集合中
with open(output_zc_file, 'r', encoding='utf-8') as f:
    zc_set = set(line.strip() for line in f)

temp_list = []  # 使用列表保持 All.txt 的原始顺序
temp_set_dedup = set()  # 用于去重检查
bm_repe_set = set()  # 用于记录当前转换过程中已使用的编码

with open('jdAllx.csv', 'r', encoding='utf-8') as file:
    for line in file:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith('#'):
            temp_list.append(stripped_line)
            continue

        parts = stripped_line.split('\t')
        if len(parts) != 2:
            continue
        word, line_bm = parts

        # 核心排除逻辑：如果词组已存在于 .dict.yaml 中，直接跳过整个词组
        if word in zc_set:
            continue

        # 处理词组 3 字, 3码空码动态匹配到 6 码
        if len(word) == 3:
            # 检查编码是否在 .dict.yaml 或当前转换中已存在，如果存在就顺延
            if line_bm[0:3] not in bm_set and line_bm[0:3] not in bm_repe_set:
                entry = f"{word}\t{line_bm[0:3]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
                    bm_repe_set.add(line_bm[0:3])
            elif line_bm[0:4] not in bm_set and line_bm[0:4] not in bm_repe_set:
                entry = f"{word}\t{line_bm[0:4]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
                    bm_repe_set.add(line_bm[0:4])
            elif line_bm[0:5] not in bm_set and line_bm[0:5] not in bm_repe_set:
                entry = f"{word}\t{line_bm[0:5]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
                    bm_repe_set.add(line_bm[0:5])
            elif line_bm[0:6] not in bm_set and line_bm[0:6] not in bm_repe_set:
                entry = f"{word}\t{line_bm[0:6]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
                    bm_repe_set.add(line_bm[0:6])
            else:
                # 3、4、5、6码都被占用（.dict.yaml或当前转换中），放在6码位置（允许重码）
                entry = f"{word}\t{line_bm[0:6]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
        # 处理其它长度的字词, 4码空码动态匹配到 6 码
        else:
            # 检查编码是否在 .dict.yaml 或当前转换中已存在，如果存在就顺延
            if line_bm[0:4] not in bm_set and line_bm[0:4] not in bm_repe_set:
                entry = f"{word}\t{line_bm[0:4]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
                    bm_repe_set.add(line_bm[0:4])
            elif line_bm[0:5] not in bm_set and line_bm[0:5] not in bm_repe_set:
                entry = f"{word}\t{line_bm[0:5]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
                    bm_repe_set.add(line_bm[0:5])
            elif line_bm[0:6] not in bm_set and line_bm[0:6] not in bm_repe_set:
                entry = f"{word}\t{line_bm[0:6]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)
                    bm_repe_set.add(line_bm[0:6])
            else:
                # 4、5、6码都被占用（.dict.yaml或当前转换中），放在6码位置（允许重码）
                entry = f"{word}\t{line_bm[0:6]}"
                if entry not in temp_set_dedup:
                    temp_list.append(entry)
                    temp_set_dedup.add(entry)

content = '''---
name: xkjd6.result
version: "v1"
sort: original
...
'''

with open('./result.dict.yaml', 'w', encoding='utf-8') as outfile:
    outfile.write(content)
    for line in temp_list:  # 使用 temp_list 保持 All.txt 的原始顺序
        outfile.write(line+"\n")




