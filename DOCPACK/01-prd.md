---
title: Book Grant Data — Product Requirements (PRD)
doc_id: BGD-DOC-01
doc_type: prd
version: 0.1
date: 2026-10-08
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
related: 00-product-card.md, 00-overview.md, 02-architecture.md, 03-nfr-security.md, 04-runbook.md
---

# Book Grant Data — Product Requirements (PRD)

## 1. ปัญหาและเป้าหมาย

**ปัญหา:** ทุนให้เปล่า (depa, SBA, Grants.gov, Innovate UK, Creative Europe, National Lottery ฯลฯ)
กระจายอยู่หลายเว็บ เงื่อนไขคุณสมบัติ เส้นตาย และภาระรายงานอ่านยาก และหลายหน้าเป็นเพียง
"สารบบโครงการ" ไม่ใช่รอบรับสมัครที่เปิดอยู่จริง

**เป้าหมายผลิตภัณฑ์:** ให้ข้อมูลทุนที่ตรวจย้อนได้ (มี lineage ถึง bytes ต้นฉบับ) แยก "ไม่รู้" ออกจาก
"เป็นเท็จ" และแยก program directory ออกจากทุนจริง เพื่อให้ consumer กรองทุนที่เปิดอยู่ได้อย่างซื่อตรง

**เป้าหมายตาม roadmap (สถานะ `proposed`):** ภายใน 2026-12-31 เปลี่ยนจาก local source pilot เป็น
monitored product — ทั้ง 7 แหล่งมี permission basis ลงทะเบียนใน parent, มี freshness SLO ที่ parent
monitor ตรวจ, schedule ทุก 6 ชั่วโมงรัน 7 วันโดยไม่มี failure ที่อธิบายไม่ได้ และ `grant.v2`
ลงทะเบียนใน metadata catalog/lineage

## 2. ผู้ใช้และ persona

| Persona | ความต้องการ | สถานะหลักฐาน |
|---|---|---|
| Operator (เจ้าของ Solo Empire) | ค้นทุนที่เปิดอยู่สำหรับธุรกิจ solo ของตน เช่น depa | ผู้ใช้จริงคนเดียวในปัจจุบัน **[ต้องยืนยัน]** |
| Consumer ภายใน (`discovery.portfolio.v1`) | อ่าน record ผ่าน domain CLI contract แบบ read-only | มีใน parent |
| Freelancer / SME / ทีมเล็ก | digest ทุนรายสัปดาห์ | เป้าหมายอนาคต **[สมมติฐาน]** |

## 3. ขอบเขต

**In scope**

- ทุนโครงการ (project funding call) หมวด research, innovation, arts-culture, community, small-business, climate
- metadata ระดับโครงการ: ผู้ให้ทุน, ประเทศที่มีสิทธิ์, ข้อความคุณสมบัติ, สถานะ, เส้นตาย, ชนิดมูลค่า,
  ค่าใช้จ่าย, และ domain terms (`funding_purpose`, `applicant_type`, `matching_funds_required`, `reporting_obligation`)
- การเก็บแบบ manual จากแหล่งทางการที่ตรวจทานแล้ว พร้อม lineage

**Out of scope**

- ทุนการศึกษารายบุคคล (เป็นของ scholarship) และ cohort/accelerator (เป็นของ startup-program)
- การตัดสินคุณสมบัติส่วนบุคคล, ranking, การยื่นใบสมัคร, การแจ้งเตือน, การเก็บ profile ผู้ใช้
- public mirror ของเนื้อหาต้นฉบับ, การเขียนข้อมูลเข้าฐานข้อมูลของแอปอื่น

## 4. ฟีเจอร์หลักและลำดับความสำคัญ

| ID | ฟีเจอร์ | Priority | สถานะ |
|---|---|---|---|
| FR-01 | `book-grant-data contract [--version v1\|v2]` พิมพ์ JSON Schema | Must | ทำแล้ว |
| FR-02 | `validate <file>` ตรวจ export ตาม contract (ปฏิเสธ NaN/Infinity, ข้อความว่าง/มองไม่เห็น, id ซ้ำ) | Must | ทำแล้ว |
| FR-03 | `demo --open-only / --query / --as-of` กรองทุนที่เปิดอยู่ (ตัด closed, ไม่รู้เส้นตาย, หมดอายุ, stale > 72h, future-checked) | Must | ทำแล้ว |
| FR-04 | `capture acquire [--source-id]` เก็บ bytes จาก 7 แหล่งผ่าน shared runtime | Must | ทำแล้ว (manual) |
| FR-05 | `capture records` replay record จาก landing/Bronze ที่ตรวจ checksum แล้ว | Must | ทำแล้ว |
| FR-06 | adapter ต่อแหล่ง fail closed เมื่อ source ไม่รู้จัก/หน้าเปลี่ยน/challenge page | Must | ทำแล้ว |
| FR-07 | ลงทะเบียน permission basis ใน parent coverage registry (`grt-g1`) | Must | ยังไม่ทำ |
| FR-08 | Freshness SLO และ monitor (`grt-g2`) | Must | ยังไม่ทำ |
| FR-09 | Schedule ทุก 6 ชั่วโมงที่ได้รับอนุมัติ (`grt-g3`) | Should | ยังไม่ทำ |
| FR-10 | ลงทะเบียน `grant.v2` ใน metadata catalog/lineage (`grt-g4`) | Should | ยังไม่ทำ |
| FR-11 | Consumer แรก: digest ทุนที่เปิดอยู่ (Markdown/LINE) | Could | ยังไม่ทำ **[สมมติฐาน]** |
| FR-12 | เพิ่มแหล่งไทย (NIA, สสว.) | Could | NIA ถูกปิด; สสว. ยังไม่ตรวจ **[ต้องยืนยัน]** |

## 5. ตัวชี้วัดความสำเร็จ

ยังไม่มีค่าฐาน (baseline) ใน repository ตัวชี้วัดด้านล่างเป็นข้อเสนอ

| ตัวชี้วัด | เป้าหมาย | ที่มา |
|---|---|---|
| แหล่งที่มี permission basis ลงทะเบียน | 7/7 | roadmap `grt-g1` |
| แหล่งที่ monitor รายงานสถานะ fresh/stale/quarantined | 7/7 | roadmap `grt-g2` |
| วันที่ schedule รันโดยไม่มี failure ที่อธิบายไม่ได้ | 7 วันติด | roadmap `grt-g3` |
| ผู้ใช้/consumer นอกจาก operator ภายใน 2026-Q4 | ≥ 1 | เงื่อนไขคำตัดสินใน product card |

## 6. Roadmap / phase

| Phase | เนื้อหา | สถานะ |
|---|---|---|
| P0 | contract v1, demo, validation, CI | เสร็จ |
| P1 | 7 source adapters, capture/replay, contract v2 | เสร็จ (manual) |
| P2 | permission registry, freshness SLO, schedule, catalog/lineage (`grt-t1`–`grt-t6`) | วางแผน (เป้า 2026-Q4) |
| P3 | โครง domain plugin เพื่อรับโดเมน discovery อื่น (ดู `D-01`) | ข้อเสนอ **[ต้องยืนยัน]** |
| P4 | consumer แรกและการวัดการใช้งาน | ข้อเสนอ **[สมมติฐาน]** |

## 7. Decision ที่ต้องยืนยัน

| ID | Decision | สถานะ |
|---|---|---|
| D-01 | ให้ `book-grant-data` เป็น canonical/ฐาน merge ของ discovery family: repo discovery อื่น (13 repo ที่ใช้ `cli.py`/capture scaffolding ชุดเดียวกัน) merge เข้ามาเป็น domain plugin (schema + `source-*.json`) | **[ต้องยืนยัน]** — เสนอโดย product card; ยังไม่มีการตัดสินใน roadmap หรือ architecture ของ parent |

ข้อพิจารณาสำหรับ D-01 (จากหลักฐาน):

- โค้ด `cli.py` ถูกคัดลอกใน 13 repo และ `tests/test_shared_cli.py` ตรึง sha256 ทุกสำเนา การแก้ต้องแก้ทุก repo
  (`docs/UPGRADE-PLAN.md`) — เป็นต้นทุนที่ merge จะลดได้
- `docs/UPGRADE-PLAN.md` มี backlog P1 ให้แทนสำเนาด้วย shared runtime package ที่ติดตั้งได้อิสระ — เป็นทางเลือกแทน merge
- `discovery-portfolio.md` ของ parent ปัจจุบันกำหนด domain owner แยกเป็นรายโดเมน (14 repo) การ merge จะเปลี่ยน
  ownership boundary นี้และต้องอัปเดตเอกสาร/registry ของ parent **[ต้องยืนยัน]**

## 8. ข้อสมมติฐานและความเสี่ยง

| ID | รายการ | ผลกระทบ | การลด |
|---|---|---|---|
| R-01 | หน้าเว็บต้นทางเปลี่ยนรูปแบบหรือแสดง challenge page | capture ถูก quarantine, ข้อมูล stale | required markers + fail closed; ต้องเพิ่ม marker ที่แข็งแรงขึ้นสำหรับ SBA (backlog P1) |
| R-02 | เงื่อนไขการใช้ (ToS/robots) ของแหล่งเปลี่ยน | ต้องหยุดเก็บ | `permission_evidence` ต่อแหล่ง + ทบทวนใน `grt-g1` |
| R-03 | ทุนแบบมีรอบเวลา (ZEVI 2, ปิด 2026-09-16) หมดอายุ | record ค้างใน feed | เพิ่ม source record ID ใหม่ต่อรอบ (backlog P1) |
| R-04 | ไม่มีผู้ใช้นอกจาก operator | คำตัดสินลดเป็น `showcase` | consumer แรก (FR-11) |
| R-05 | การ merge (D-01) ทำให้ boundary ของ 13 repo เปลี่ยน | งานย้ายโค้ดและ registry | ยืนยัน D-01 ก่อนเริ่ม P3 |
| A-01 | depa เป็นสารบบโครงการ ไม่ใช่รอบรับสมัคร | สถานะ `unknown` เสมอจนกว่าจะมีรอบชัด | parser เฉพาะรอบเมื่อประกาศ (backlog P2) |

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `PRODUCT.md`
- `sources.json`
- `docs/UPGRADE-PLAN.md`
- `src/book_grant_data/cli.py`
- `src/book_grant_data/capture.py`
- `DOCPACK/00-product-card.md`
- `(solo-empire) repository-catalog/roadmaps/data-scrapers.yaml` (`grt-g1`–`grt-g4`, `grt-t1`–`grt-t6`)
- `(solo-empire) systems/architecture/discovery-portfolio.md`
