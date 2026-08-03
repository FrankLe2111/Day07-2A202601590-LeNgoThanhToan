import csv
import re
from pathlib import Path

# K4
D = Path(r"C:\Users\dang_\Desktop\Python\opencv-course-master\Day07-2A202601590-LeNgoThanhToan\data\k4_ecommerce")
KEY = "customer_role"

# Nếu kiểm tra K4, thay bằng:
# D = Path("data/k4_ecommerce")
# KEY = "customer_role"

REQUIRED_FIELDS = [
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
]

md_files = sorted(D.glob("*.md"))

csv_path = D / "sources.csv"
with csv_path.open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))

doc_ids = []
roles = {}

for path in md_files:
    content = path.read_text(encoding="utf-8")

    # Lấy YAML front matter nằm giữa hai dấu ---
    parts = content.split("---", maxsplit=2)

    if len(parts) < 3:
        print(f"{path.name:40} THIEU FRONT MATTER")
        continue

    metadata = {}
    for field, value in re.findall(r"^(\w+):\s*(.+)$", parts[1], flags=re.MULTILINE):
        metadata[field] = value.strip().strip('"').strip("'")

    doc_id = metadata.get("doc_id")
    role = metadata.get(KEY)

    doc_ids.append(doc_id)

    if role:
        roles[role] = roles.get(role, 0) + 1

    has_required_fields = all(
        field in metadata and metadata[field].strip()
        for field in REQUIRED_FIELDS
    )

    is_valid = (
        has_required_fields
        and KEY in metadata
        and bool(metadata[KEY].strip())
        and doc_id == path.stem
    )

    status = "OK" if is_valid else "THIEU METADATA"
    print(f"{path.name:40} {status}")

csv_ids = [row.get("doc_id") for row in rows]

print()
print("so file :", len(md_files), "(can 5-10)")
print(
    "csv     :",
    "khop" if sorted(csv_ids) == sorted(doc_ids) else "LECH",
)
print(f"{KEY:8}:", roles)