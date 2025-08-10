import os
import requests
import zipfile
import io
from requests.auth import HTTPBasicAuth

# ===== НАСТРОЙКИ =====
AIDBOX_URL = "http://localhost:8080"
AIDBOX_BASIC_USER = "root"
AIDBOX_BASIC_PASS = "A8NTSr7BdF" # подставить из BOX_ROOT_CLIENT_SECRET из docker-compose.yaml  

ZIP_URL = "https://drive.google.com/uc?export=download&id=1brhvxmDScI4v1gHTdY4YKqPRUJ-Luv-J"
UNZIP_DIR = "./hl7_files"
BATCH_SIZE = 3
# =====================

def collect_files_recursively(root_dir):
    files = []
    for base, _, names in os.walk(root_dir):
        for n in names:
            if n.lower().endswith((".txt")):
                files.append(os.path.join(base, n))        
    return files

print("[*] Скачиваю ZIP…")
resp = requests.get(ZIP_URL)
resp.raise_for_status()

print("[*] Распаковываю…")
os.makedirs(UNZIP_DIR, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
    z.extractall(UNZIP_DIR)

files = collect_files_recursively(UNZIP_DIR)
print(f"[*] Найдено файлов: {len(files)}")

auth = HTTPBasicAuth(AIDBOX_BASIC_USER, AIDBOX_BASIC_PASS)

def make_entry_yaml(hl7_text: str) -> str:
    # отступаем HL7 под блоком |-
    indented = hl7_text.strip().replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\n        ")
    return f"""
  - request:
      method: POST
      url: Hl7v2Message
    resource:
      resourceType: Hl7v2Message
      status: received
      config:
        resourceType: Hl7v2Config
        id: default
      src: |-
        {indented}
""".rstrip()

def send_batch(batch_paths):
    entries = []
    for p in batch_paths:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            hl7 = f.read()
        entries.append(make_entry_yaml(hl7))

    body = f"""resourceType: Bundle
type: transaction
entry:
{''.join(entries)}
"""

    # печатаем тело
    print("\n===== SENDING BATCH BODY =====")
    print(body)
    print("=========== END BODY =========")

    r = requests.post(
        f"{AIDBOX_URL}/",
        auth=auth,
        headers={"Content-Type": "text/yaml"},
        data=body
    )

    print("\n===== RESPONSE =====")
    print(r.status_code, r.text)
    print("===== END RESPONSE =====")

# батчим по 3
for i in range(0, len(files), BATCH_SIZE):
    batch = files[i:i+BATCH_SIZE]
    print(f"\n[*] Отправляю батч {i//BATCH_SIZE + 1}:")
    for p in batch:
        print("   -", os.path.relpath(p, UNZIP_DIR))
    send_batch(batch)