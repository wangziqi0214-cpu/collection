#!/usr/bin/env python3
"""把用户导出的 JSON 合并回收藏链接.md(保留远程新增)
用法: python3 merge_user_export.py <用户导出的.json>
"""
import re, sys, json, datetime, pathlib

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
                link = ln.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif ln.startswith(">"):
                desc = ln[1:].strip()
        entries.append({"date": date, "title": title, "src": src, "link": link, "desc": desc})
    return entries

def main():
    if len(sys.argv) < 2:
        print("用法: merge_user_export.py <export.json>")
        sys.exit(1)
    user_entries = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    md_text = SRC.read_text(encoding="utf-8")
    remote = parse_entries(md_text)
    remote_keys = {(e["date"], e["title"]) for e in remote}

    added = []
    for e in user_entries:
        key = (e.get("date", ""), e.get("title", ""))
        if key not in remote_keys:
            added.append(e)

    if not added:
        print("没有需要新增的条目(用户数据都已存在)")
        return

    # 生成新块,追加到 md 末尾(按日期分组)
    blocks = []
    for e in added:
        lines = [f"### [{e.get('date','')}] {e.get('title','')}"]
        if e.get("src"):
            lines.append(f"> 来源：{e['src']}")
        if e.get("link"):
            lines.append(f"> 链接：{e['link']}")
        if e.get("desc"):
            lines.append(f"> {e['desc']}")
        blocks.append("\n".join(lines))
    new_section = "\n\n\n" + "\n\n\n".join(blocks) + "\n"

    # 在文件末尾追加
    with open(SRC, "a", encoding="utf-8") as f:
        f.write(new_section)
    print(f"已合并 {len(added)} 条用户新增到 {SRC}")

if __name__ == "__main__":
    main()
