"""Render reports/findings.md to a styled, paginated US-Letter PDF."""
import pathlib, markdown
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
EXE = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
md = (ROOT/"findings.md").read_text()
html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
CSS = """
*{box-sizing:border-box}
body{font-family:-apple-system,system-ui,"Segoe UI",Roboto,sans-serif;color:#17181a;
  line-height:1.55;max-width:760px;margin:0 auto;padding:8px 4px;font-size:13.5px}
h1{font-family:Georgia,ui-serif,serif;font-size:26px;line-height:1.12;margin:0 0 6px;letter-spacing:-.01em}
h2{font-family:Georgia,ui-serif,serif;font-size:19px;margin:26px 0 8px;padding-top:8px;
  border-top:2px solid #eceae4;break-after:avoid}
h3{font-size:15px;margin:18px 0 6px;color:#b4531f;break-after:avoid}
p,li{font-size:13.5px}
strong{font-weight:650}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;background:#f1f0ec;
  padding:1px 4px;border-radius:4px}
pre{background:#f7f6f2;border:1px solid #e6e4dd;border-radius:8px;padding:12px 14px;
  overflow-x:auto;font-size:11.5px;line-height:1.5;break-inside:avoid}
pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:12px;break-inside:avoid}
th,td{border:1px solid #e2e0d9;padding:5px 9px;text-align:left;vertical-align:top}
th{background:#f2f1ec;font-weight:650}
blockquote{margin:14px 0;padding:10px 16px;background:#fbf3ee;border-left:3px solid #d9662f;
  border-radius:0 8px 8px 0;color:#4a4640;break-inside:avoid}
blockquote p{margin:0;font-size:12.5px}
hr{border:0;border-top:1px solid #e2e0d9;margin:20px 0}
a{color:#b4531f;word-break:break-word}
@page{size:Letter;margin:15mm 16mm}
"""
doc = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
       f'<body>{html_body}</body></html>')
src = ROOT/"_findsrc.html"; src.write_text(doc)
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    pg = b.new_page(color_scheme="light")
    pg.goto(src.resolve().as_uri()); pg.wait_for_timeout(400)
    pg.pdf(path=str(ROOT/"UES_Legionnaires_technical_findings.pdf"),
           format="Letter", print_background=True,
           margin={"top":"15mm","bottom":"16mm","left":"16mm","right":"16mm"})
    b.close()
src.unlink(missing_ok=True)
print("wrote reports/UES_Legionnaires_technical_findings.pdf")
