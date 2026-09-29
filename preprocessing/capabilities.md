# capabilities.md —— 本机 / 本 agent 能力自报

> CLI 探测不到的五维能力边界，开工前自报（`references/preprocessing.md` §1.1）。
> 自报日期：2026-09-29。

| 维度 | 自报 | 对本书的影响 |
|---|---|---|
| agent 自身能力 | **multimodal=是**（可用 Read 读页图/截图做视觉兜底）；**search=可用但本轮未使用**（WebSearch/WebFetch 可查证史实专名；`references/web/`、`references/user/` 为空，无查证留痕） | 本书有文字层、无 OCR 需求；专名/史实可按需联网核对 |
| agent 模型 | DeepSeek-V4-Flash-0731（前置 4 单元与 ch05–ch10 初译）／DeepSeek-V4.1-Flash（ch01–ch03 首译、ch04 对齐重建、交付修复） | 严格按单元喂入，禁止整本读入 |
| OS 环境 | pandoc / pdftotext / pymupdf / tesseract / rapidocr / java / epubcheck 全可用（doctor 通过） | PDF 文字层走 pymupdf；pdftotext 作 RTL 校验 oracle |
| 外部 API 边界 | `MINERU_API_KEY` 已配置（但本书非扫描件，**不使用 MinerU**） | 不产生外部上传 |
| 待处理文件工作量 | 267 页 / 约 65.3 万字符 / 约 13.2 万波斯语词 / 17 个单元；**翻译难度高**（15 世纪古典波斯语） | 单批约 3k 字符，估 ≈220 批 |
| 持久化统一库 | `knowledge path` 可写（默认 `~/Documents/auto-epublizer`，私有 git） | 术语经 `knowledge export/import` 跨书复用 |

## 技术前提（已核实）

- 源 PDF **有完整文字层**（第 4–266 页），仅 4 张图（封面/封底/1 个小 logo）→ **不需 OCR / MinerU**。
- 文字层为 **RTL**：PyMuPDF 原生输出词序颠倒、含呈现形字符与双向控制符。
  **已为本机 CLI 补 RTL 支持**（`feat/rtl-extraction` 分支，386 tests 全绿，
  见 `preprocessing/plan.md`），抽取词序与 `pdftotext` oracle 一致率 **95.7%**。
