import os
import ast
from datetime import datetime

MEMES_DIR = "./memes"
OUTPUT_DIR = "./docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "meme_keywords.md")

# GitHub 仓库信息 - 用于 Wiki 链接
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "jinjiao007/meme-generator-jj")


def extract_meme_info(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except Exception as e:
        print(f"❌ 解析失败 {file_path}: {e}")
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'add_meme':
            info = {
                "keywords": [],
                "min_images": None,
                "min_texts": None,
                "default_texts": [],
                "date_created": None,
            }
            for kw in node.keywords:
                if kw.arg == 'keywords' and isinstance(kw.value, ast.List):
                    info["keywords"] = [elt.s for elt in kw.value.elts if isinstance(elt, ast.Str)]
                elif kw.arg == 'min_images' and isinstance(kw.value, ast.Constant):
                    info["min_images"] = kw.value.value
                elif kw.arg == 'min_texts' and isinstance(kw.value, ast.Constant):
                    info["min_texts"] = kw.value.value
                elif kw.arg == 'default_texts' and isinstance(kw.value, ast.List):
                    info["default_texts"] = [elt.s for elt in kw.value.elts if isinstance(elt, ast.Str)]
                elif kw.arg == 'date_created' and isinstance(kw.value, ast.Call) and getattr(kw.value.func, 'id', '') == 'datetime':
                    args = [a.n for a in kw.value.args if isinstance(a, ast.Constant)]
                    if len(args) >= 3:
                        info["date_created"] = datetime(*args)
            return info
    return None


def find_first_image_path(subdir):
    images_dir = os.path.join(subdir, "images")
    if not os.path.isdir(images_dir):
        return None

    for file in sorted(os.listdir(images_dir)):
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            return os.path.join(images_dir, file).replace("\\", "/")
    return None


def generate_markdown_table(modules_info, previews_by_module):
    lines = [
        "| # | 预览 | 关键词 | 图片 | 文字 | 默认文字 | 模块 | 创建日期 |",
        "|:--:|:----:|:------:|:------:|:------:|:------:|:----------:|:------:|"
    ]
    for idx, (module, info) in enumerate(modules_info, 1):
        kw_str = "</br>".join(info["keywords"]) if info["keywords"] else "&nbsp;"
        module_link = f"[{module}](https://github.com/{GITHUB_REPO}/tree/master/memes/{module})"
        date_str = info["date_created"].strftime("%Y-%m-%d") if info["date_created"] else "&nbsp;"
        image_count = str(info.get("min_images")) if info.get("min_images") is not None else "&nbsp;"
        text_count = str(info.get("min_texts")) if info.get("min_texts") is not None else "&nbsp;"
        default_texts = "</br>".join(t.replace("\n", "</br>") for t in info["default_texts"]) if info["default_texts"] else "&nbsp;"
        preview = f'<div style="text-align:center"><img src="{previews_by_module.get(module)}" height="50" width="50" style="object-fit:cover;"></div>' if module in previews_by_module else "&nbsp;"
        lines.append(f"| {idx} | {preview} | {kw_str} | {image_count} | {text_count} | {default_texts} | {module_link} | {date_str} |")
    return "\n".join(lines)


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    modules_info = []
    previews_by_module = {}

    for folder in os.listdir(MEMES_DIR):
        subdir = os.path.join(MEMES_DIR, folder)
        init_file = os.path.join(subdir, "__init__.py")

        if os.path.isdir(subdir) and os.path.isfile(init_file):
            info = extract_meme_info(init_file)
            if info:
                modules_info.append((folder, info))
                image_path = find_first_image_path(subdir)
                if image_path:
                    # 使用 GitHub raw 链接，让 Wiki 能正确显示图片
                    # 去掉路径开头的 './' 
                    clean_path = image_path.lstrip("./")
                    github_raw_path = f"https://raw.githubusercontent.com/{GITHUB_REPO}/master/{clean_path}"
                    previews_by_module[folder] = github_raw_path

    # 按创建时间倒序
    modules_info.sort(key=lambda x: x[1]["date_created"] or datetime.min, reverse=True)
    meme_count = len(modules_info)
    header = f"# ✨Meme Keywords\n\n**🎈总表情数：{meme_count}**\n"
    
    # 添加CSS样式来固定列宽
    css_style = """
<style>
table {
    table-layout: fixed;
    width: 100%;
}
table th:nth-child(1) { width: 50px; }   /* # */
table th:nth-child(2) { width: auto; }   /* 预览 */
table th:nth-child(3) { max-width: 180px; }   /* 关键词 */
table th:nth-child(4) { width: 70px; }   /* 图片 */
table th:nth-child(5) { width: 70px; }   /* 文字 */
table th:nth-child(6) { max-width: 180px;  }   /* 默认文字 */
table th:nth-child(7) { width: auto; }  /* 模块 */
table th:nth-child(8) { width: 135px; }  /* 创建日期 */
</style>
"""
    
    markdown_table = generate_markdown_table(modules_info, previews_by_module)
    markdown = header + "\n" + css_style + "\n\n" + markdown_table

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"✅ 输出完成：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
