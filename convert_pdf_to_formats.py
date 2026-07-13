import csv
import html
import urllib.request
from pathlib import Path

from openpyxl import Workbook
from pypdf import PdfReader

base_name = 'Gistda_Price_List'
pdf_path = Path(f'{base_name}.pdf')
url = 'https://www.gistda.or.th/download/Gistda_Price_List.pdf'

if not pdf_path.exists():
    with urllib.request.urlopen(url, timeout=60) as resp:
        pdf_path.write_bytes(resp.read())

reader = PdfReader(str(pdf_path))
rows = []
for page_num, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ''
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        lines = ['[No text extracted]']
    for line_num, line in enumerate(lines, start=1):
        rows.append({'page': page_num, 'line': line_num, 'text': line})

csv_path = Path(f'{base_name}.csv')
with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['page', 'line', 'text'])
    writer.writeheader()
    writer.writerows(rows)

xlsx_path = Path(f'{base_name}.xlsx')
wb = Workbook()
ws = wb.active
ws.title = 'Content'
ws.append(['page', 'line', 'text'])
for row in rows:
    ws.append([row['page'], row['line'], row['text']])
wb.save(xlsx_path)

html_path = Path(f'{base_name}.html')
html_rows = ''.join(
    f'<tr><td>{html.escape(str(r["page"]))}</td><td>{html.escape(str(r["line"]))}</td><td>{html.escape(r["text"])}</td></tr>'
    for r in rows
)
html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{base_name}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>{base_name}</h1>
  <table>
    <thead>
      <tr><th>Page</th><th>Line</th><th>Text</th></tr>
    </thead>
    <tbody>{html_rows}</tbody>
  </table>
</body>
</html>
'''
html_path.write_text(html_content, encoding='utf-8')

print('Created:')
print(csv_path)
print(xlsx_path)
print(html_path)
print('Rows:', len(rows))
