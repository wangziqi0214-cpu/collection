#!/usr/bin/env python3
"""把用户导出的 JSON 合并回收藏链接.md(保留远程新增),并同步分类映射 categories.json
用法: python3 merge_user_export.py <用户导出的.json>
"""
import re, sys, json, pathlib

SRC = pathlib.Path.home() / "Documents/收藏/收藏链接.md"

def parse_entries(md_text):
    entries = []
    blocks = re.split(r"\n### ", md_text)[1:]
    for b in blocks:
        lines = b.split("\n")
        title_line = lines[0].strip()
        m = re.match(r"\[(\d{4}-\d{2}-\d{2})\]\s*(.+)", title_line)
        if not m:
            continue
        date, title = m.group(1), m.group(2)
        src, link, desc = "", "", ""
        for ln in lines[1:]:
            ln = ln.strip()
            if ln.startswith("> 来源：") or ln.startswith("> 来源:"):
                src = ln.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif ln.startswith("> 链接：") or ln.startswith("> 链接:") or ln.startswith("> GitHub:") or ln.startswith("> GitHub："):
                # 正则提取冒号后的完整内容(兼容全角/半角),避免 split 吃掉 https:
                m2 = re.match(r">\s*(?:链接|GitHub)[：:]\s*(.+)", ln)
                link = m2.group(1).strip() if m2 else ln.split("：", 1)[-1].split(":", 1)[-1].strip()
                # 清理多余斜杠: https:////xxx -> https://xxx
                link = re.sub(r"^https?:///+", "https://", link)
            elif ln.startswith(">"):
                desc = ln[1:].strip()
        entries.append({"date": date, "title": title, "src": src, "link": link, "desc": desc})
    return entries

def clean_link(link):
    link = (link or "").strip()
    if not link.startswith("http"):
        link = "https://" + link
    return re.sub(r"^https?:///+", "https://", link)

def main():
    if len(sys.argv) < 2:
        print("用法: merge_user_export.py <export.json>")
        sys.exit(1)
    user_entries = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    md_text = SRC.read_text(encoding="utf-8")
    remote = parse_entries(md_text)
    remote_keys = {(e["date"], e["title"]) for e in remote}

    cats_file = pathlib.Path(__file__).parent / "categories.json"
    try:
        cats = json.loads(cats_file.read_text(encoding="utf-8"))
    except Exception:
        cats = {}

    # 分类变更回写:用户导出的 category 与现存映射不同 → 更新
    cat_changed = 0
    for e in user_entries:
        cat = (e.get("category") or "").strip()
        if not cat:
            continue
        key = f"{e.get('date', '')}|{e.get('title', '')}"
        if (e.get('date', ''), e.get('title', '')) in remote_keys and cats.get(key) != cat:
            cats[key] = cat
            cat_changed += 1

    added = []
    for e in user_entries:
        key = (e.get("date", ""), e.get("title", ""))
        if key not in remote_keys:
            added.append(e)
            cat = (e.get("category") or "").strip()
            if cat:
                cats[f"{key[0]}|{key[1]}"] = cat

    if added:
        # 生成新块,追加到 md 末尾(按日期分组)
        blocks = []
        for e in added:
            lines = [f"### [{e.get('date','')}] {e.get('title','')}"]
            if e.get("src"):
                lines.append(f"> 来源：{e['src']}")
            if e.get("link"):
                lines.append(f"> 链接：{clean_link(e['link'])}")
            if e.get("desc"):
                lines.append(f"> {e['desc']}")
            blocks.append("\n".join(lines))
        new_section = "\n\n\n" + "\n\n\n".join(blocks) + "\n"
        with open(SRC, "a", encoding="utf-8") as f:
            f.write(new_section)

    if cat_changed or any((e.get("category") or "").strip() for e in added):
        cats_file.write_text(json.dumps(cats, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"已合并 {len(added)} 条用户新增到 {SRC};分类更新 {cat_changed} 条 → {cats_file}")

if __name__ == "__main__":
    main()
