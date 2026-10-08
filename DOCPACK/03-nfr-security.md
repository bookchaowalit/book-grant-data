---
title: Book Grant Data — NFR และความปลอดภัย
doc_id: BGD-DOC-03
doc_type: nfr-security
version: 0.1
date: 2026-10-08
status: ร่างเพื่อพิจารณา
owner: Solution Architect + Security (Book Dev)
related: 00-overview.md, 01-prd.md, 02-architecture.md, 04-runbook.md
---

# Book Grant Data — NFR และความปลอดภัย

## 1. สรุป

ระบบเป็น local pilot ที่ไม่มี service ออนไลน์ NFR จึงเน้นความสดของข้อมูล คุณภาพข้อมูล
การเคารพเงื่อนไขของแหล่ง และการไม่เก็บข้อมูลส่วนบุคคล ตัวเลขที่ "บังคับใช้แล้ว" มาจากโค้ด
ส่วนเป้าหมายที่ยังไม่ได้บังคับใช้ระบุสถานะไว้ชัด

## 2. เป้าหมาย NFR ที่วัดได้

| ID | หมวด | ข้อกำหนด | ค่าเป้าหมาย | สถานะ / หลักฐาน |
|---|---|---|---|---|
| NFR-01 | Freshness | `--open-only` ตัด record ที่ตรวจเก่ากว่ากำหนด | 72 ชั่วโมง (ค่า default `max_age_hours`) | บังคับใช้ใน `cli.py` `filter_items` |
| NFR-02 | Freshness | ทบทวนแหล่งทุก 24 ชั่วโมง | 24h | เป้าหมายใน `PRODUCT.md`; ยังไม่มี schedule |
| NFR-03 | Freshness SLO | parent monitor รายงาน fresh/stale/quarantined ต่อแหล่ง | 7/7 แหล่ง | ยังไม่ทำ (`grt-g2`) |
| NFR-04 | Source load | ช่วงห่างขั้นต่ำต่อแหล่ง | 21,600 วินาที (6 ชม.) ใน `min_interval_seconds` ทุกแหล่ง | บังคับใช้โดย shared runtime + file lock |
| NFR-05 | Source load | จำนวนครั้ง/timeout/ขนาด | ≤ 2 GET, 15 วินาทีต่อครั้ง, ≤ 2 MB | บังคับใช้ใน `capture_runtime.py` |
| NFR-06 | Capacity | record ต่อ envelope | ≤ 10,000 | ระบุใน `PRODUCT.md` |
| NFR-07 | Data quality | export ผ่าน JSON Schema และกฎเพิ่ม (ไม่รับ NaN/Infinity, ข้อความว่าง/มองไม่เห็น, id ซ้ำ, `live` ต้องมี lineage) | 100% ของ record | บังคับใช้ใน `validate` + tests |
| NFR-08 | Data quality | หน้าเปลี่ยน/challenge page ไม่ถูกรับเป็นข้อมูล | markers ครบทุกตัว มิฉะนั้น quarantine | บังคับใช้; markers ของ SBA ยังอ่อน (backlog P1) |
| NFR-09 | Correctness | เวลาปิดรับแบบ UK แปลงเป็น UTC โดยไม่ขึ้นกับ locale | ครอบคลุม BST/GMT | tests ใน `tests/test_source.py` |
| NFR-10 | Availability | ไม่มี SLA (ไม่มี service) | — | ระบุใน `PRODUCT.md` "no live SLA" |
| NFR-11 | Portability | CLI contract รันได้โดยไม่มี parent | Python 3.10 และ 3.13 | CI matrix |

## 3. Performance และ scalability

- ข้อมูลระดับหลักสิบ record (7 แหล่ง × ~1 record ต่อแหล่งในปัจจุบัน) การกรองเป็น in-memory
- การขยายโดเมน/แหล่งทำได้โดยเพิ่ม `source-*.json` + adapter; ข้อจำกัดหลักคือ cooldown และงานตรวจสิทธิ์ ไม่ใช่ compute
- ไม่มีการวัด latency **[ต้องยืนยัน]** ว่าจำเป็นหรือไม่เมื่อมี consumer

## 4. Licensing / ToS ของแหล่ง

| Source ID | การเข้าถึง | หลักฐานสิทธิ์ (`permission_evidence`) | ทบทวนล่าสุด |
|---|---|---|---|
| `govuk-innovation-funding` | GOV.UK Content API | นโยบาย reuse GOV.UK — Crown copyright, OGL v3.0 | 2026-09-07 |
| `depa-digital-startup-fund` | HTML | อ้างเฉพาะ URL หน้าเว็บ ไม่มีเอกสารเงื่อนไข **[ต้องยืนยัน]** | 2026-09-07 |
| `iuk-zevi2-alternative-fuels` | HTML | อ้างเฉพาะ URL หน้าเว็บ **[ต้องยืนยัน]** | 2026-09-07 |
| `grants-gov-research-opportunities` | HTML | robots.txt | 2026-09-08 |
| `creative-europe-culture-calls` | HTML | robots.txt | 2026-09-08 |
| `national-lottery-community-funding` | HTML | robots.txt | 2026-09-08 |
| `sba-small-business-grants` | HTML | robots.txt | 2026-09-08 |

หลักการ: ทุกแหล่งมี `permission_status: reviewed-public-read` และ `use` = metadata สำหรับ
personal discovery, "no source-body republication" การ robots.txt อนุญาตไม่เท่ากับการอนุญาตให้
นำไปใช้เชิงพาณิชย์ — หากทำ digest ขาย (FR-11) ต้องทบทวน ToS ของแต่ละแหล่งก่อน **[ต้องยืนยัน]**
แหล่ง NIA ถูกปิดจนกว่าจะมี API/export ทางการ

## 5. Security controls

- Network: HTTPS GET อ่านอย่างเดียว, ไม่ follow redirect โดยอัตโนมัติ (ต้องทบทวน policy), ไม่ retry เมื่อได้ 429/auth failure
- ไม่ใช้ credential, cookie หรือบัญชีผู้ใช้ใด ๆ; ปฏิเสธการ archive เมื่อพบ session-token marker
- Source ID selector ปฏิเสธ path traversal และ ID ที่ไม่รู้จัก (`tests/test_registry.py`)
- `validate` ไม่ echo เนื้อหา input ออกทาง error และไม่บันทึกไฟล์
- `.gitignore` กัน `data/`, `logs/`, `.env*`, `credentials/` ไม่ให้เข้า Git
- Supply chain: `jsonschema` และ `ruff` pin version; GitHub Actions ใช้ `permissions: contents: read`

## 6. Privacy / PDPA

- ข้อมูลเป็น metadata สาธารณะของโครงการทุนเท่านั้น ไม่มี profile ผู้ใช้ ใบสมัคร คำตอบคัดกรอง หรือข้อมูลการเงินส่วนบุคคล
- การตัดสินคุณสมบัติส่วนบุคคลเป็นหน้าที่ของ consumer ที่มี private storage แยก (README)
- หน้าเว็บต้นฉบับอาจมีชื่อ/อีเมลผู้ติดต่อของหน่วยงาน — bytes ดิบเก็บใน private local archive เท่านั้นและไม่ถูกดึงเป็น field
  **[สมมติฐาน]** ควรยืนยันว่าไม่มีข้อมูลบุคคลหลุดเข้า Bronze metadata
- Retention: "private local raw archive; operational retention; no automatic deletion" — ยังไม่มีกำหนดระยะเก็บเป็นตัวเลข **[ต้องยืนยัน]**

## 7. Observability

- ปัจจุบัน: control state ต่อแหล่ง (เวลาตรวจ, quarantine) และ exit code ของคำสั่ง
- ยังไม่มี: log rotation, alert, dashboard; parent coverage registry ยังไม่รวม grant (`observed_gaps` ใน roadmap)
- เป้าหมาย: log ของ schedule มีเฉพาะจำนวนสถานะต่อแหล่ง ไม่มี payload (`grt-t3`)

## 8. Backup / DR

- โค้ด/contract/source policy: อยู่ใน Git remote
- `data/lake` และ `data/control`: อยู่บนเครื่อง operator เท่านั้น ไม่มี backup ที่บันทึกไว้ **[ต้องยืนยัน]**
- DR: เนื่องจากแหล่งเป็นสาธารณะ การสูญเสีย lake กู้ได้ด้วยการ acquire ใหม่ แต่จะเสีย history ของ bytes เดิม

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Solution Architect (Book Dev) | รอพิจารณา | — | ________ |
| Security reviewer | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `PRODUCT.md`
- `sources.json`
- `src/book_grant_data/source.json`, `src/book_grant_data/source-*.json`
- `src/book_grant_data/cli.py`
- `tests/test_registry.py`
- `.gitignore`
- `.github/workflows/ci.yml`
- `docs/UPGRADE-PLAN.md`
- `(solo-empire) infra/scripts/discovery/capture_runtime.py`
- `(solo-empire) repository-catalog/roadmaps/data-scrapers.yaml`
