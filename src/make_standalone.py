"""Wrap artifact-body HTML (which the claude.ai host normally wraps) into a
COMPLETE standalone document with a doctype + viewport, so the file opens in
standards mode and looks/behaves correctly when opened or shared directly."""
import pathlib, sys, re
ROOT = pathlib.Path(__file__).resolve().parent.parent/"reports"
def wrap(src, dst):
    body = (ROOT/src).read_text()
    m = re.search(r"<title>(.*?)</title>", body)
    title = m.group(1) if m else "Report"
    doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           f'<title>{title}</title>\n</head>\n<body>\n{body}\n</body>\n</html>\n')
    (ROOT/dst).write_text(doc)
    print(f"wrote reports/{dst}")
for src, dst in [("map.html","map_standalone.html"),
                 ("public_report.html","public_report_standalone.html")]:
    wrap(src, dst)
