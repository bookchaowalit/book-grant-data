---
title: Book Grant Data — Runbook การรันและดูแลระบบ
doc_id: BGD-DOC-04
doc_type: runbook
version: 0.1
date: 2026-10-08
status: ร่างเพื่อพิจารณา
owner: DevOps / Operator (Book Dev)
related: 00-overview.md, 01-prd.md, 02-architecture.md, 03-nfr-security.md
---

# Book Grant Data — Runbook การรันและดูแลระบบ

## 1. Environments

| Environment | ใช้ทำอะไร | สถานะ |
|---|---|---|
| Local offline | contract, validate, demo, tests | ใช้งานได้ |
| Local capture | acquire/records ผ่าน shared runtime ของ parent | ใช้งานได้ (manual) |
| CI (GitHub Actions) | ruff + pytest offline + CLI smoke | ใช้งานได้ |
| Scheduled / production | — | ไม่มี |

## 2. Build และทดสอบ

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
python -m pytest -q
book-grant-data contract --version v2 > /dev/null
book-grant-data validate src/book_grant_data/demo.json
book-grant-data demo --open-only
```

ไม่มีขั้นตอน deploy: ไม่มี container, ไม่มี hosting, ไม่มี runtime port การ "ปล่อย" คือ merge เข้า `main` ให้ CI ผ่าน

## 3. Scheduled runs

- ปัจจุบัน **ไม่มี schedule** (`sources.json` notes: "No schedule or remote writes")
- แผน (`grt-g3`): ใช้ Windows Task Scheduler ทุก 6 ชั่วโมงผ่าน
  `(solo-empire) infra/scripts/discovery/setup_windows_task.ps1` — ติดตั้งได้เฉพาะเมื่อเจ้าของเครื่องอนุมัติ
  ตรวจสถานะด้วย `powershell.exe -File infra/scripts/discovery/setup_windows_task.ps1 status`
- ระหว่างนี้ใช้คำสั่งรวมของ parent: `task discovery -- acquire` แล้ว `task discovery -- status`

## 4. Manual capture (acquire) และ replay

ตั้ง `SOLO_EMPIRE_ROOT` ให้ชี้ checkout ของ Solo Empire บนเครื่อง (README ตัวอย่างใช้ path
`/home/bookchaowalit/book/solo-empire` ซึ่งต่างจาก checkout ปัจจุบัน **[ต้องยืนยัน]** path ที่ถูกต้อง)

```bash
PY="$SOLO_EMPIRE_ROOT/infra/.venv-datalake/bin/python"
# ทุกแหล่งที่เปิด
PYTHONPATH=src "$PY" -m book_grant_data.capture acquire --lake "$PWD/data/lake" --state-dir "$PWD/data/control"
# แหล่งเดียว
PYTHONPATH=src "$PY" -m book_grant_data.capture acquire --source-id depa-digital-startup-fund --lake "$PWD/data/lake" --state-dir "$PWD/data/control"
# replay record จาก lake (ไม่ใช้ network)
PYTHONPATH=src "$PY" -m book_grant_data.capture records --lake "$PWD/data/lake" --state-dir "$PWD/data/control"
# ดู control state
PYTHONPATH=src "$PY" -m book_grant_data.capture status --lake "$PWD/data/lake" --state-dir "$PWD/data/control"
```

`acquire` เป็นงาน network ที่ต้องตั้งใจสั่ง; `records` และ `status` อ่าน local state เท่านั้น

## 5. Backfill / replay

- Replay: `records` สร้าง record ใหม่จาก landing/Bronze ที่ตรวจ checksum แล้ว ใช้หลังแก้ adapter โดยไม่ต้องดึงซ้ำ
- Backfill ย้อนหลังจากแหล่งทำไม่ได้: แหล่งเป็นหน้าเว็บสถานะปัจจุบัน ไม่มี history API **[สมมติฐาน]**
- แหล่งที่ bytes ไม่เปลี่ยนจะใช้ batch เดิม (idempotent) แต่ control state บันทึกเวลาตรวจใหม่
- ทุนแบบมีรอบ (เช่น ZEVI 2 ปิด 2026-09-16): เพิ่ม source record ID ใหม่สำหรับรอบใหม่ ห้ามแก้ history เดิม

## 6. Config และ secret

| ชื่อตัวแปร | ใช้ทำอะไร |
|---|---|
| `SOLO_EMPIRE_ROOT` | path ของ parent ที่มี `infra/scripts/discovery/capture_runtime.py` |
| `PYTHONPATH` | ชี้ `src` เมื่อรันโดยไม่ติดตั้ง package |

ไม่มี secret, token หรือ credential — ทุกแหล่งเป็น public read

## 7. Health check

```bash
book-grant-data contract --version v2 > /dev/null && echo contract-ok
PYTHONPATH=src "$PY" -m book_grant_data.capture status --lake "$PWD/data/lake" --state-dir "$PWD/data/control"
task discovery -- list --domain grant          # จาก parent
task discovery -- coverage --domain grant      # จาก parent
```

สัญญาณปกติ: ทุกแหล่งมีเวลาตรวจไม่เกิน 72 ชั่วโมงและไม่มีสถานะ quarantine ที่ไม่มีคำอธิบาย

## 8. Failure handling / troubleshooting

| อาการ | สาเหตุที่เป็นไปได้ | การแก้ |
|---|---|---|
| `Set SOLO_EMPIRE_ROOT ...` (exit 2) | ไม่ได้ตั้งตัวแปร | ตั้ง `SOLO_EMPIRE_ROOT` |
| `Shared discovery runtime is unavailable.` | path ผิด/parent ไม่มี runtime | ตรวจ checkout ของ parent |
| `unsupported shared capture runtime` | runtime VERSION ≠ 1 | ใช้ runtime เวอร์ชันที่ตรง หรืออัปเดต adapter |
| `unknown source id` / `unknown grant source` | ID ไม่อยู่ใน policy | ตรวจ `sources.json` และ `source-*.json` |
| `generic grant source drift or challenge page` | หน้าเปลี่ยนหรือถูกบล็อก | capture ถูก quarantine; เปิดหน้าด้วยมือ ตรวจ markers แล้วแก้ `required_markers` พร้อม test |
| `source disallowed by robots` | robots.txt เปลี่ยน | หยุดใช้แหล่งนั้น และบันทึกใน `sources.json` |
| ไม่ดึงใหม่ | อยู่ใน cooldown 6 ชั่วโมง | รอ; ห้ามลด `min_interval_seconds` โดยไม่ทบทวน |
| 429 / auth failure | แหล่งจำกัดการเข้าถึง | runtime ไม่ retry; รอรอบถัดไปและทบทวนสิทธิ์ |
| `demo --open-only` ว่าง | ทุกแหล่ง stale/ไม่รู้เส้นตาย | ปกติสำหรับสารบบโครงการ (depa) ตรวจ `--as-of` |

ไม่มี fallback ไปใช้ fixture หรือผลสำเร็จครั้งก่อน การล้มเหลวต้องแสดงเป็นสถานะไม่ใช่ถูกซ่อน

## 9. Rollback

- โค้ด/contract: revert commit แล้วให้ CI ผ่าน; contract ที่เปลี่ยนแบบ breaking ต้องออกเวอร์ชันใหม่
- ข้อมูล: landing/Bronze เป็น immutable; rollback คือ replay ด้วย adapter เวอร์ชันก่อน
- ไม่มี production deployment ให้ rollback

## 10. Backup / restore

- ไม่มีขั้นตอน backup ของ `data/lake` และ `data/control` ที่บันทึกไว้ **[ต้องยืนยัน]**
- Restore แบบขั้นต่ำ: acquire ใหม่จากแหล่ง (history ของ bytes เดิมจะหาย)
- การลบข้อมูลเก่าเป็นงาน manual ตาม data lifecycle policy ของ repository ไม่มีการลบอัตโนมัติ

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| DevOps / Operator (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `sources.json`
- `src/book_grant_data/capture.py`
- `.github/workflows/ci.yml`
- `docs/UPGRADE-PLAN.md`
- `(solo-empire) infra/scripts/discovery/capture_runtime.py`
- `(solo-empire) systems/architecture/discovery-portfolio.md`
- `(solo-empire) repository-catalog/roadmaps/data-scrapers.yaml`
