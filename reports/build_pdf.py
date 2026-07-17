"""Render public_report.html to a shareable, paginated US-Letter PDF
(light theme, backgrounds preserved). Requires playwright + the bundled Chromium."""
import pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
EXE = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
body = (ROOT/"public_report.html").read_text()
doc = "<!doctype html><html><head><meta charset=utf-8></head><body>"+body+"</body></html>"
src = ROOT/"_pdfsrc.html"; src.write_text(doc)
PRINT_CSS = """
:root{color-scheme:light}
.pg{padding:0 !important;background:#fff !important}
.wide{max-width:680px !important}
.mapcard,.callout,.symp,.limits,.fc,.cbar,figure{break-inside:avoid;page-break-inside:avoid}
h1,h2,h3{break-after:avoid}
@page{size:Letter;margin:14mm 15mm}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    pg = b.new_page(viewport={"width":820,"height":1100}, color_scheme="light")
    pg.goto(src.resolve().as_uri())
    pg.evaluate("document.documentElement.setAttribute('data-theme','light')")
    pg.add_style_tag(content=PRINT_CSS)
    pg.wait_for_timeout(800)
    pg.emulate_media(media="screen")
    pg.pdf(path=str(ROOT/"UES_Legionnaires_explainer.pdf"), format="Letter",
           print_background=True,
           margin={"top":"14mm","bottom":"16mm","left":"15mm","right":"15mm"})
    b.close()
src.unlink(missing_ok=True)
print("wrote reports/UES_Legionnaires_explainer.pdf")
