---
title: Book Grant Data — ภาพรวมระบบและสารบัญเอกสาร
doc_id: BGD-DOC-00
doc_type: overview
version: 0.1
date: 2026-10-08
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
related: 00-product-card.md, 01-prd.md, 02-architecture.md, 03-nfr-security.md, 04-runbook.md
---

# Book Grant Data — ภาพรวมระบบและสารบัญเอกสาร

## 1. สรุประบบ

`book-grant-data` เป็น data product ขนาดเล็ก (Python) สำหรับค้นหาทุนให้เปล่าที่ไม่แลกหุ้น
(non-equity project funding) พร้อมเงื่อนไขและภาระรายงาน ระบบเก็บหน้าเว็บ/API ทางการจาก
7 แหล่งที่ตรวจทานแล้วแบบ manual ผ่าน shared capture runtime ของ Solo Empire
(landing bytes → Bronze manifest) แล้ว replay เป็น record ตาม contract `grant.v2`
และให้ CLI `book-grant-data` ตรวจ/กรอง record แบบอ่านอย่างเดียว ข้อมูลที่ไม่รู้ (จำนวนเงิน,
เส้นตาย, คุณสมบัติ) คงเป็น `null`/`unknown` เสมอ ไม่มีการเดา

## 2. สถานะปัจจุบัน

| รายการ | สถานะ (ตรวจจาก repository) |
|---|---|
| ระยะ | local source pilot (`PRODUCT.md` status `local-source-pilot`) |
| Contract | `grant.v1` (demo/validation) และ `grant.v2` (record ที่ capture จริง) |
| แหล่งข้อมูลที่เปิดใช้ | 7 แหล่งใน `sources.json` (`source.json` = GOV.UK + `source-*.json` อีก 6 ไฟล์) |
| แหล่งที่ถูกปิด | `nia-financial-support` (หน้าเกิน 2 MB และมี CSRF marker) |
| CI | GitHub Actions `ci.yml`: ruff, pytest แบบ offline, CLI smoke บน Python 3.10/3.13 |
| Schedule | ไม่มี; การ acquire เป็นคำสั่ง manual |
| Deploy / Live URL | ไม่มี; ไม่มี runtime port |
| Consumer | local portfolio CLI ใน parent (`task discovery -- list`) เท่านั้น |

หมายเหตุ: product card ระบุ "6 ไฟล์ `source-*.json` (README อ้าง 7 แหล่ง)" ตรวจแล้ว
แหล่งที่ 7 คือ `govuk-innovation-funding` ซึ่งอยู่ในไฟล์ `source.json` (ไม่มีคำนำหน้า `source-`)
จำนวน 7 จึงตรงกับ `sources.json`

## 3. ผู้ใช้หลัก

- Operator คนเดียวของ Solo Empire (เจ้าของ repo) ที่ใช้ค้นทุนสำหรับธุรกิจตนเอง
- Consumer ภายใน: `discovery.portfolio.v1` ใน parent ที่อ่าน domain CLI contract
- ผู้ใช้ภายนอก (freelancer/SME) เป็นเป้าหมายในอนาคต **[ต้องยืนยัน]**

## 4. รายการเอกสาร

| รหัส | ไฟล์ | ชื่อ | ผู้อ่านหลัก |
|---|---|---|---|
| CARD-book-grant-data | `00-product-card.md` | Product Card (คำตัดสิน `invest`) | Product owner |
| BGD-DOC-00 | `00-overview.md` | ภาพรวมระบบและสารบัญเอกสาร | ทุกคน |
| BGD-DOC-01 | `01-prd.md` | Product Requirements (PRD) | Product owner |
| BGD-DOC-02 | `02-architecture.md` | System Architecture | Solution Architect, Data |
| BGD-DOC-03 | `03-nfr-security.md` | NFR และความปลอดภัย | Solution Architect, Security |
| BGD-DOC-04 | `04-runbook.md` | Runbook การรันและดูแลระบบ | DevOps / Operator |

## 5. วิธีอ่าน

1. เริ่มที่ Product Card เพื่อดูคำตัดสินและเหตุผล
2. อ่าน PRD เพื่อดูขอบเขต ฟีเจอร์ และ decision `D-01` เรื่องการเป็นฐาน merge ของ discovery family
3. อ่าน Architecture และ NFR เพื่อเข้าใจเส้นทาง source → landing → Bronze → CLI และข้อจำกัดด้าน ToS/PDPA
4. ใช้ Runbook เมื่อต้อง acquire, replay หรือแก้ปัญหา

ป้าย **[ต้องยืนยัน]** คือข้อเท็จจริงที่เจ้าของต้องยืนยัน และ **[สมมติฐาน]** คือสมมติฐานทำงาน

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `PRODUCT.md`
- `sources.json`
- `src/book_grant_data/source.json`
- `.github/workflows/ci.yml`
- `DOCPACK/00-product-card.md`
- `(solo-empire) systems/architecture/discovery-portfolio.md`
