# 貢獻指南

歡迎新增主題、模版、資訊圖表元件或工作流。這份文件依照「想做的事」分段，挑你需要的看就好。

> English: the same steps apply — `deckframes themes new`, edit the JSON, preview with
> `deckframes themes gallery --only <name>`, then open a PR. Skills and CLI messages are English.

- [開發環境](#開發環境)
- [新增主題](#新增主題)
- [新增 .pptx 模版](#新增-pptx-模版)
- [新增資訊圖表元件](#新增資訊圖表元件)
- [新增工作流 skill](#新增工作流-skill)
- [PR 檢查清單](#pr-檢查清單)

---

## 開發環境

```bash
git clone https://github.com/ChienIKao/deckframes && cd deckframes
pip install -e ".[preview]" pytest
pytest -q
```

預覽需要 PowerPoint（Windows）或 LibreOffice。`deckframes doctor` 會列出缺什麼。程式架構見 [`AGENTS.md`](AGENTS.md)。

---

## 新增主題

主題是一個 JSON 檔，描述配色、字型、邊框和陰影。canvas 引擎依照它畫出所有頁面：大綱、章節子目錄、導覽列、資訊圖表。

### 1. 建立

```bash
deckframes themes new my-lab                  # 複製 blockframe → ~/.deckframes/themes/my-lab.json
deckframes themes new my-lab --from capsule   # 從其他主題複製
deckframes themes new my-lab --project        # 寫到目前資料夾的 themes/，只給這個專案用
```

也可以從 HyperFrames 的設計開始：`deckframes themes import <preset>`，再手動微調。

### 2. 修改

打開 JSON，常改的欄位如下（檔案裡的 `_edit` 也有提示）：

| 欄位 | 用途 |
|---|---|
| `colors.ground` | 投影片背景 |
| `colors.text`、`colors.black` | 內文、框線與連接線（通常是同一個深色） |
| `colors.muted` | 次要文字 |
| `colors.palette` | 2–5 個強調色，元件會輪流使用；第一個夠淺的色（從第 4 個開始找）會當螢光筆色 |
| `colors.chapter_cycle` | 各章的代表色（章節頁、導覽列），預設同 `palette` |
| `fonts` | `display` 標題、`label` 標籤、`body` 內文、`ea` 中文、`code` 程式碼 |
| `stroke` | `border`／`thin` 框線粗細、`shadow`／`thin_shadow` 硬陰影位移，單位 pt，0 = 不要 |
| `decorations`、`tilt` | 星爆、斜紋、點陣裝飾／卡片傾斜 |
| `sizes` | 字級（pt） |

- 色碼不用加 `#`。
- 色塊上的文字會自動在深色與白色間切換，不用擔心對比。
- 字型請選簡報電腦上一定有的（Office 內建字型最保險），否則 PowerPoint 會自動替換。

### 3. 預覽

```bash
deckframes themes gallery --only my-lab                      # 單一主題
deckframes themes gallery --only blockframe,my-lab           # 和其他主題並排比較
deckframes build examples/demo.md --theme my-lab -o my-lab.pptx && deckframes check my-lab.pptx
```

用 `examples/demo.md` 檢查所有元件，`check` 要 0 issue。

### 4. 使用或分享

| 目的 | 做法 |
|---|---|
| 自己用 | 放在 `~/.deckframes/themes/`，之後用 `--theme my-lab` 或在 front matter 寫 `theme: my-lab` |
| 給同事 | 直接傳 JSON，對方放進自己的 `~/.deckframes/themes/` |
| 貢獻成內建主題 | 見下方 |

### 5. 貢獻成內建主題（PR）

1. 把 JSON 移到 `src/deckframes/themes/<name>.json`，刪掉 `_edit` 和 `based_on`，寫好 `description`。
2. 在 [`skills/deckframes-design/SKILL.md`](skills/deckframes-design/SKILL.md) 的內建主題表加一列。
3. 重新產生 README 的主題一覽：
   ```bash
   deckframes themes gallery --presets --out docs/themes-gallery.png
   python -c "from PIL import Image; Image.open('docs/themes-gallery.png').convert('RGB').save('docs/themes-gallery.jpg', quality=80, optimize=True)"
   ```
   刪掉 png，只提交 jpg。
4. 主題名稱用小寫英文、數字、連字號。改編自別人的設計時，要在 `description` 註明來源，並確認對方的授權允許。

---

## 新增 .pptx 模版

模版會完整保留公司或學校的母片，但**沒有大綱、章節子目錄和導覽列**，資訊圖表也會變成條列和表格。要這些功能，請改做主題。

```bash
mkdir -p ~/.deckframes/templates/my-school
cp school.pptx ~/.deckframes/templates/my-school/template.pptx
deckframes template inspect ~/.deckframes/templates/my-school/template.pptx \
  --write-config ~/.deckframes/templates/my-school/config.json
```

檢查 `config.json` 的 `layouts`（角色 → 版面名稱）是否正確，然後：

```bash
deckframes build talk.md --template my-school
```

各欄位說明見 [`skills/deckframes-templates/SKILL.md`](skills/deckframes-templates/SKILL.md)。

- 分享時把整個資料夾（`template.pptx` + `config.json`）交給對方即可。
- **模版不收進本 repo。** 母片通常有版權或機構識別規範；如果有自動判斷版面的改進，歡迎改 `engines/template.py` 的 `ROLE_KEYWORDS`。

---

## 新增資訊圖表元件

以新增一個 `pyramid` 元件為例，需要改這幾個地方：

| 檔案 | 修改 |
|---|---|
| `src/deckframes/markdown.py` | 把名稱加進 `COMPONENT_TYPES`，讓 ```` ```pyramid ```` 被解析成元件（項目語法沿用 `make_item`） |
| `src/deckframes/engines/canvas.py` | 新增 `comp_pyramid(self, s, d, x, y, w, h)`。只能用主題 token（`self.color_for(k)`、`self.on(fill)`、`self.block(...)`），不要寫死顏色 |
| `src/deckframes/layout.py` | 在 `degrade()` 決定模版模式下要退化成什麼（條列或表格） |
| `skills/deckframes-infographics/SKILL.md` | 在對照表和語法表加一列：什麼內容適合用它 |
| `skills/deckframes-core/SKILL.md` | 在元件清單加上名稱 |
| `examples/demo.md` | 加一張示範投影片 |
| `tests/test_smoke.py` | 確認 demo 建置後 `check` 為 0 issue |

完成後用 `deckframes themes gallery` 確認各主題都正常，特別是深色與淺色的 palette。

---

## 新增工作流 skill

工作流是給 AI 看的做事流程，例如「論文口試」「募資簡報」。

1. 建立 `skills/deckframes-<name>/SKILL.md`：
   ```markdown
   ---
   name: deckframes-<name>
   description: >
     一段英文說明：這是什麼工作流、什麼時候用。AI 工具會根據這段話決定要不要載入。
   ---
   ```
2. 內容參考 [`deckframes-academic-defense`](skills/deckframes-academic-defense/SKILL.md)：章節結構、內容轉換規則、驗收重點。
3. 在入口 skill [`skills/deckframes/SKILL.md`](skills/deckframes/SKILL.md) 的「Route」表加一列，並在 README 的 Skills 一覽加一列。
4. 規則：
   - 用英文寫
   - 不提任何 AI 產品專屬的工具名稱（要讓 Claude Code、Codex 等工具都能用）
   - 所有動作都透過 `deckframes` CLI 完成

---

## PR 檢查清單

- [ ] `pytest -q` 全部通過
- [ ] `ruff check --select F,E9 src tests` 沒有錯誤
- [ ] `deckframes build examples/demo.md` 後 `deckframes check` 為 0 issue
- [ ] 改到外觀時，附上 `deckframes themes gallery` 或 `deckframes preview` 的截圖
- [ ] 範例內容是虛構的，不含個人或機構的真實資料
- [ ] 相關的 skill 與 README 已同步更新
