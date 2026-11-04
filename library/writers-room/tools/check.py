#!/usr/bin/env python3
"""Проверка сценариев и сборка index.csv.

python3 tools/check.py                 # проверить все episodes/*.md
python3 tools/check.py E001 E002       # только эти
python3 tools/check.py --index         # проверить всё и записать index.csv
"""
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EP = ROOT / "episodes"
CAST = set(re.findall(r"\|\s*(ch_\w+)\s*\|", (ROOT / "cast.md").read_text()))
PLACES = set(re.findall(r"\|\s*(pl_\w+)\s*\|", (ROOT / "places.md").read_text()))
FORMATS = dict(re.findall(r"^## (F\d\d)\. (.+)$", (ROOT / "formats.md").read_text(), re.M))

BANNED = [
    # страны и части света
    r"\bросси", r"\bказахстан", r"\bузбекистан", r"\bкыргызстан", r"\bкиргиз", r"\bтаджикистан", r"\bтуркмен",
    r"\bамерик", r"\bсша\b", r"\bкита[йея]", r"\bяпони", r"\bгерман", r"\bфранц", r"\bитали", r"\bиспани",
    r"\bтурци", r"\bинди[яию]\b", r"\bевроп", r"\bукраин", r"\bбеларус", r"\bбелорус", r"\bмонгол", r"\bкорея", r"\bбритан", r"\bангли[яию]\b",
    r"\bмоскв", r"\bалмат", r"\bташкент", r"\bбишкек", r"\bастан", r"\bнью-йорк", r"\bпариж", r"\bлондон",
    # политика
    r"президент", r"депутат", r"парламент", r"\bвыборы\b", r"предвыбор", r"\bпартии? власти", r"премьер-министр", r"губернатор",
    # религия
    r"\bбог(а|у|ом|е|и|ов|ам)?\b", r"аллах", r"церк", r"мечет", r"\bхрам", r"молитв", r"молить", r"\bрай\b", r"\bад\b", r"\bгрех", r"священ", r"батюшк", r"\bимам", r"рамадан", r"пасх", r"рождеств", r"намаз",
    # марки
    r"apple", r"iphone", r"айфон", r"google", r"гугл", r"яндекс", r"\bсбер\b", r"сбербанк", r"tesla", r"тесл[аы]", r"instagram", r"инстаграм",
    r"tiktok", r"тикток", r"telegram", r"телеграм", r"whatsapp", r"ватсап", r"chatgpt", r"чатгпт", r"netflix", r"нетфликс",
    r"amazon", r"амазон", r"uber", r"\bубер", r"coca", r"кока-кол", r"pepsi", r"пепси", r"mcdonald", r"макдон", r"ikea", r"икеа",
    r"samsung", r"самсунг", r"microsoft", r"майкрософт", r"windows", r"excel", r"эксел", r"youtube", r"ютуб", r"facebook", r"фейсбук",
    r"lego", r"\bлего\b", r"nike", r"найк", r"adidas", r"адидас", r"wildberries", r"вайлдбер", r"ozon", r"озон", r"kaspi", r"каспи", r"авито",
]
BANNED_RE = re.compile("|".join(BANNED), re.I)
FIELDS = ["Формат", "Длительность", "Логлайн", "Персонажи", "Места", "Лучшая реплика"]
WORD = re.compile(r"[\wё-]+", re.I)


def words(t):
    return len([w for w in WORD.findall(t) if w != "-"])


def parse(path):
    text = path.read_text()
    errs = []
    m = re.match(r"# (E\d{3})\. (.+)\n", text)
    if not m:
        return None, ["нет заголовка «# E001. Название»"]
    eid, title = m.group(1), m.group(2).strip()
    if eid != path.stem:
        errs.append(f"id {eid} не совпадает с файлом {path.name}")
    meta = {}
    for f in FIELDS:
        mm = re.search(rf"^- \*\*{f}:\*\* (.+)$", text, re.M)
        if not mm:
            errs.append(f"нет поля «{f}»")
        else:
            meta[f] = mm.group(1).strip()
    fm = re.match(r"(F\d\d)", meta.get("Формат", ""))
    fid = fm.group(1) if fm else None
    if fid not in FORMATS:
        errs.append(f"неизвестный формат {meta.get('Формат')}")
    else:
        n = int(eid[1:])
        expect = f"F{(n - 1) // 6 + 1:02d}"
        if fid != expect:
            errs.append(f"{eid} должен быть формата {expect}, а не {fid}")
    dm = re.match(r"(\d+)", meta.get("Длительность", ""))
    dur = int(dm.group(1)) if dm else 0
    if not 35 <= dur <= 60:
        errs.append(f"длительность {dur} вне 35–60")
    chars = re.findall(r"ch_\w+", meta.get("Персонажи", ""))
    places = re.findall(r"pl_\w+", meta.get("Места", ""))
    for c in chars:
        if c not in CAST:
            errs.append(f"персонажа {c} нет в cast.md")
    for p in places:
        if p not in PLACES:
            errs.append(f"места {p} нет в places.md")
    if not chars:
        errs.append("пустой список персонажей")
    if not places:
        errs.append("пустой список мест")
    rows = [l for l in text.splitlines() if re.match(r"\|\s*\d+\s*[–-]\s*\d+\s*\|", l)]
    if len(rows) < 6:
        errs.append(f"в таблице тактов {len(rows)} строк, нужно ≥ 6")
    prev = 0
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(cells) != 7:
            errs.append(f"строка не из 7 колонок: {r[:60]}")
            continue
        a, b = map(int, re.findall(r"\d+", cells[0])[:2])
        if a != prev:
            errs.append(f"разрыв времени: {prev} → {a}")
        if b <= a:
            errs.append(f"плохой интервал {cells[0]}")
        prev = b
        line = cells[3]
        if line not in ("—", "-", ""):
            w = words(line)
            lim = 2.5 * (b - a) + 1
            if w > lim:
                errs.append(f"{cells[0]}: {w} слов на {b - a} с (максимум {int(lim)}): {line[:50]}")
    if rows and prev != dur:
        errs.append(f"таблица кончается на {prev} с, а длительность {dur} с")
    lm = re.search(r"^\*\*Последняя реплика:\*\* (.+)$", text, re.M)
    if not lm:
        errs.append("нет строки «**Последняя реплика:** …»")
    for bm in BANNED_RE.finditer(text):
        errs.append(f"запретное слово: «{text[max(0, bm.start() - 15):bm.end() + 15]}»")
    rec = dict(id=eid, format=fid or "", format_name=FORMATS.get(fid, ""), title=title,
               characters=" ".join(chars), places=" ".join(places), duration=dur,
               best_line=meta.get("Лучшая реплика", "").strip("«»\" "),
               last_line=lm.group(1).strip() if lm else "")
    return rec, errs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    files = sorted(EP.glob("E*.md")) if not args else [EP / f"{a}.md" for a in args]
    recs, bad = [], 0
    for f in files:
        rec, errs = parse(f)
        if errs:
            bad += 1
            print(f"✗ {f.name}")
            for e in errs:
                print("   ", e)
        if rec:
            recs.append(rec)
    print(f"проверено {len(files)}, с ошибками {bad}")
    if "--index" in sys.argv:
        with open(ROOT / "index.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "format", "format_name", "title", "characters", "places", "duration_s", "best_line"])
            for r in recs:
                w.writerow([r["id"], r["format"], r["format_name"], r["title"], r["characters"], r["places"], r["duration"], r["best_line"]])
        print("index.csv:", len(recs))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
