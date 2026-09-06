from pathlib import Path
from pypdf import PdfReader

ROOT = Path(r"D:\专升本学习")
PDF_DIR = ROOT / "tmp_openstax"
BOOKS = [
    ("Calculus Volume 1", "Calculus_Volume_1.pdf", "https://openstax.org/details/books/calculus-volume-1"),
    ("Calculus Volume 2", "Calculus_Volume_2.pdf", "https://openstax.org/details/books/calculus-volume-2"),
    ("Calculus Volume 3", "Calculus_Volume_3.pdf", "https://openstax.org/details/books/calculus-volume-3"),
]

for title, pdf_name, source in BOOKS:
    pdf_path = PDF_DIR / pdf_name
    out_dir = ROOT / "高数" / title
    out_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(pdf_path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.replace("\x00", "")
        pages.append(f"\n\n<!-- Page {index} -->\n\n{text.strip()}")
    md = "\n".join([
        f"# {title}",
        "",
        "> OpenStax official complete textbook converted from the publisher PDF.",
        "> License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).",
        f"> Source: {source}",
        f"> Original PDF pages: {len(reader.pages)}",
        "> Conversion note: text was extracted page by page. Mathematical notation, equation layout, figures, and some multi-column reading order may not survive plain Markdown conversion; consult the official PDF for exact presentation.",
        "",
        "---",
        "",
        "\n".join(pages).strip(),
        "",
    ])
    (out_dir / f"{title}.md").write_text(md, encoding="utf-8")
    print(f"{title}: {len(reader.pages)} pages -> {out_dir / (title + '.md')}")
