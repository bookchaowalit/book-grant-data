---
title: Book Grant Data — Product Card
doc_id: CARD-book-grant-data
doc_type: product-card
verdict: invest
version: 0.1
date: 2026-10-08
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
---

# Book Grant Data — Product Card

## 1. สรุปคุณค่าในหนึ่งประโยค

ช่วยคนทำงานอิสระและทีมเล็ก (รวมถึงธุรกิจของเจ้าของเอง) ค้นหาทุนให้เปล่าที่ไม่แลกหุ้น พร้อมเงื่อนไขและภาระรายงาน จากแหล่งทางการที่ตรวจทานแล้ว

## 2. ปัญหาและผู้ใช้เป้าหมาย

- ปัญหา: ทุน (depa, SBA, Grants.gov, Innovate UK ฯลฯ) กระจายหลายเว็บ เงื่อนไขคุณสมบัติ เส้นตาย และภาระรายงานอ่านยาก
- ผู้ใช้เป้าหมาย: freelancer/SME/ทีมเล็ก; ผู้ใช้จริงตอนนี้คือ operator คนเดียว **[ต้องยืนยัน]**

## 3. สิ่งที่ทำได้จริงตอนนี้

- CLI `book-grant-data`: `contract`, `demo --open-only` (กรองที่ปิด/ไม่รู้เส้นตาย/stale ออก), `validate` ตาม `grant.v1`
- live lane ใช้ `schema-v2.json` แยก "ไม่รู้" ออกจาก "เป็นเท็จ" และแยก program directory ออกจากทุนจริง
- `capture.py` เก็บแบบ manual จาก 6 ไฟล์ `source-*.json`: depa digital startup fund, SBA, Grants.gov, Innovate UK ZEVI2, Creative Europe, National Lottery (README อ้าง 7 แหล่ง **[ต้องยืนยัน]**)
- มี test สำหรับ contract, registry, shared CLI, source และ text extraction

## 4. หลักฐานสถานะ

| รายการ | ค่า (ตรวจจาก repository) |
|---|---|
| Stack | Python |
| Commits | 11 (แรก 2026-09-09 → ล่าสุด 2026-10-01) |
| Source | 9 ไฟล์ / 915 บรรทัด |
| Tests | 5 ไฟล์ |
| CI | 1 workflow |
| Deploy config | ไม่มี |
| Live URL | ไม่มี |
| README | 143 บรรทัด (`book-grant-data`) |
| โครงสร้างซ้ำ (template family) | 13 repo ที่มี structure signature เดียวกัน |

## 5. คุณค่าและจุดต่าง

- ทุนเป็นโดเมนที่มูลค่าต่อการค้นพบหนึ่งครั้งสูงที่สุดในกลุ่ม discovery และตรงกับธุรกิจ solo ของเจ้าของเอง (เช่น depa) **[สมมติฐาน]**
- วินัยข้อมูล: ไม่รวม value kind ต่างชนิดเป็นเงินสด, ไม่เดาคุณสมบัติ/เส้นตาย, label `live` ต้องมี lineage
- มุมรายได้: digest ทุนรายสัปดาห์สำหรับ SME ไทย หรือบริการช่วยเขียนข้อเสนอทุน **[สมมติฐาน]**

## 6. ช่องว่างสำคัญ

- ยังเป็น local source pilot: ไม่มี schedule ที่สังเกตได้ ไม่มี freshness SLO และไม่มี consumer/UI
- แหล่งไทยมีเพียง depa แหล่งเดียว; ต้องเพิ่ม (เช่น NIA, สสว.) **[ต้องยืนยัน]** สิทธิ์การเก็บข้อมูล
- โค้ด CLI/capture ซ้ำกับอีก 13 repo ใน discovery portfolio

## 7. คำตัดสิน

**`invest`** — ปัญหาจริง มี core ที่ทำงาน (capture → lake replay → CLI ค้นหา) และ roadmap มี goal ชัด (เป็น monitored product ภายใน 2026-12-31) จึงเสนอให้เป็น canonical/ฐานของผลิตภัณฑ์ discovery รวม ที่ repo อื่นใน discovery portfolio (13 repo) merge เข้ามาเป็น domain plugin จะลดเป็น `showcase` ถ้าภายใน 2026-Q4 ไม่มีผู้ใช้นอกจาก operator หรือไม่มี consumer อ่าน feed

## 8. ขั้นต่อไป

1. ทำ goal `grt-g1`–`grt-g3` ใน roadmap: ลงทะเบียน permission basis, freshness SLO, schedule 7 วันไม่มี failure ที่อธิบายไม่ได้
2. ออกแบบโครง domain plugin (schema + `source-*.json`) เพื่อรับโดเมนอื่น
3. ทำ consumer แรก: digest ทุนที่เปิดอยู่ (Markdown/LINE) แล้ววัดว่ามีคนใช้จริง

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `PRODUCT.md`
- `sources.json`
- `src/book_grant_data/cli.py`
- `src/book_grant_data/capture.py`
- `(solo-empire) systems/architecture/discovery-portfolio.md`
- `(solo-empire) repository-catalog/roadmaps/data-scrapers.yaml`
