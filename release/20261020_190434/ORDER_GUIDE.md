# astable_multivibrator — 下单指南
> 生成于 2026-10-20 19:04 JST · release_id: rel_20261020_190434
> 本目录是「准备下单」的总包。所有文件已就绪，按下面任一 Path 操作即可。

---

## 板子状态摘要
| 项 | 值 |
|---|---|
| 板厚 / 层数 | ? mm / ? layers |
| 板尺寸 | ? |
| 元件数 | 15（其中 SMT 15，THT 0） |
| 唯一 MPN 数 | 0 |
| Gerber 文件 ✓ | pcb_fab/astable_multivibrator_fab.zip |
| 生产 BOM ✓ | pcb_fab/assembly_bom.csv |
| 采购 BOM ✓ | procurement/bom_astable_multivibrator.csv |
| check-pcb gate | PASS @ 2026-10-20T10:04:01.032719Z |

---

## 用户下单偏好（Phase 2 已问，本次直接用）

| 轴 | 选项 |
|---|---|
| 渠道 | **自动选最便宜 lane**（按 coverage_scan 算法） |
| 品牌 | any |
| 价格 vs 库存 | stable_first |
| 黑名单 MPN | （无） |
| 偏好录入时间 | 2026-10-20T10:03:51+00:00 |

> 想换偏好：跑 `record_preferences.py` 重写 `_artifacts/component_selecting/user_preferences.json`，然后重跑 release。

---

## 下单 Path 选择

**渠道偏好为"自动"，按 coverage_scan 推荐：无单仓全覆盖，需 mix。**

### Path A：JLCPCB 一站式（PCB + SMT 装配）
**适合**：所有 SMT 元件都能在 LCSC 找到（覆盖率见 `coverage_matrix.md`）
**当前覆盖率**：LCSC 0/0 ⚠ 不全
**步骤**：
1. 浏览器打开 https://cart.jlcpcb.com/quote
2. 上传 `pcb_fab/astable_multivibrator_fab.zip`
3. 启用 "PCB Assembly"
4. 上传生产 BOM：`pcb_fab/assembly_bom.csv`
5. 上传 CPL：`pcb_fab/astable_multivibrator_positions.csv`
6. 工艺参数：板厚 ? mm / 铜厚 1 oz / 阻焊绿 / 丝印白（详见 `fab_options.md`）

### Path B：PCBWay turnkey（PCB + 全球采购装配）
**适合**：元件分散在 DigiKey/Mouser，LCSC 覆盖不全
**步骤**：
1. https://www.pcbway.com/orderonline.aspx
2. 上传 `pcb_fab/astable_multivibrator_fab.zip`
3. Quote Assembly → 上传 `procurement/bom_astable_multivibrator.csv`（PCBWay 接受全球 MPN）
4. CPL：`pcb_fab/astable_multivibrator_positions.csv`

### Path C：PCB 独打 + 元件自买（最便宜，但要自己焊）
PCB 走 Path A 但**不勾装配**。元件按以下任一 distributor 下：

#### C-1：DigiKey JP（覆盖率 0/0）
1. 打开 https://www.digikey.jp/en/mylists/list/bulk-add
2. 上传 `procurement/digikey_bulk.csv`
3. 缺件需走 Mouser 或 LCSC 补（详见 `coverage_matrix.md`）


#### C-2：Mouser JP（覆盖率 0/0）
1. 打开 https://www.mouser.jp/Bom/
2. 上传 `procurement/mouser_bom.csv`

#### C-3：LCSC（覆盖率 0/0）
1. 打开 https://www.lcsc.com/bom
2. 上传 `procurement/lcsc_bom.csv`
3. 注意国际运费

---

## 文件夹完整索引
- `pcb_fab/` — 给 fab 厂用：Gerber/Drill/CPL/生产 BOM
- `procurement/` — 给 distributor 用：采购 BOM + 各家上传格式 CSV
- `datasheets/` — 所有 MPN 的数据手册（焊接 / debug 时查 pin 用）
- `docs/` — kidoc 产出的 HDD / Manufacturing Transfer Pack
- `coverage_matrix.md` — 各 distributor 库存覆盖率明细
- `fab_options.md` — JLCPCB vs PCBWay 工艺对比
- `release_rel_20261020_190434.zip` — 总包，发邮件 / 转给同事用这个

---

## 红线
- ❌ 不要直接给 fab 厂源工程目录里的 `.kicad_pcb` / `.kicad_sch` —— 用 `pcb_fab/` 下的 zip
- ❌ 板子没过 check-pcb gate 不要进 release（本指南只在 gate pass 后生成）
- ❌ MPN 替换后必须重跑 release（不要只手改 csv）
