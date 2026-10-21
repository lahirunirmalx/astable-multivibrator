# Fab Vendor 选项（JLCPCB vs PCBWay）

> 来源：`.claude/skills/fab/references/jlcpcb.md` / `.claude/skills/fab/references/pcbway.md`
> 生成于 2026-10-20 19:04 JST

## 工艺对比

| 项目 | JLCPCB | PCBWay |
|---|---|---|
| 最小线宽 / 间距 | 3.5 mil / 3.5 mil | 3 mil / 3 mil |
| 最小孔径 | 0.2 mm（带铜） | 0.15 mm（激光钻） |
| 板厚范围 | 0.4–2.0 mm | 0.2–6.0 mm |
| 铜厚 | 1oz–2oz（标） / 4oz 加价 | 1oz–6oz |
| 阻焊颜色 | 绿/红/黄/蓝/白/黑 | 绿/红/黄/蓝/白/黑/紫/哑光黑 |
| 装配方式 | SMT 元件需在 LCSC 库 | turnkey（全球采购） |
| 起订 | 5 片 | 5 片 |

## 当前板子的 turnkey 适配

- LCSC 覆盖率：0/0 → **JLCPCB turnkey 不全，建议 PCBWay 或 PCB 独打 + 自买元件**
- DigiKey JP 覆盖率：0/0
- Mouser JP 覆盖率：0/0

## 用户偏好驱动的推荐

Phase 2 渠道偏好：**自动选最便宜 lane**

LCSC 覆盖率 0/0：
- LCSC 不全，自动选 PCBWay 或 PCB 独打

完整 fab vendor 规则：`.claude/skills/release/references/fab_internals.md` 或工作区 CLAUDE.md。
