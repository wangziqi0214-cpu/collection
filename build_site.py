#!/usr/bin/env python3
"""收藏链接.md → 收藏管理系统 index.html(注入数据)
用法: python3 build_site.py [输出目录]
"""
import re, sys, json, datetime, pathlib

SRC = pathlib.Path.home() / "Documents/收藏/收藏链接.md"
TEMPLATE = pathlib.Path(__file__).parent / "index.html"
OUT_DIR = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp/collection_site")

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
            elif ln.startswith("> 链接") or ln.startswith("> GitHub"):
                # 提取冒号后的完整内容(兼容全角/半角冒号)
                m2 = re.match(r">\s*(?:链接|GitHub)[：:]\s*(.+)", ln)
                link = m2.group(1).strip() if m2 else ln.split(":", 1)[-1].strip()
                if not link.startswith("http"):
                    link = "https://" + link
                # 清理多余斜杠: https:////xxx -> https://xxx
                link = re.sub(r"^https?:///+", "https://", link)
            elif ln.startswith(">"):
                desc = ln[1:].strip()
        entries.append({"date": date, "title": title, "src": src, "link": link, "desc": desc})
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries

def main():
    md_text = SRC.read_text(encoding="utf-8")
    entries = parse_entries(md_text)
    today = datetime.date.today().strftime("%Y-%m-%d")
    for e in entries:
        e["_fileDate"] = today
    data_json = json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
    template = (TEMPLATE).read_text(encoding="utf-8")
    # 用正则替换 <script id="data"> 内容(兼容模板已被注入真数据的情况,不再依赖 __DATA__ 占位符)
    page, n = re.subn(
        r'(<script id="data"[^>]*>)(.*?)(</script>)',
        lambda m: m.group(1) + data_json + m.group(3),
        template, count=1, flags=re.S,
    )
    if n == 0:
        # 兼容旧模板:替换 __DATA__ 占位符
        page = template.replace("__DATA__", data_json)
    out = OUT_DIR / "index.html"
    out.write_text(page, encoding="utf-8")
    print(f"OK: {out} | {len(entries)} 条 | {len(page)} 字节")

if __name__ == "__main__":
    main()
