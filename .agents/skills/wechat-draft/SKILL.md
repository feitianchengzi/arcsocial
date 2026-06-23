---
name: wechat-draft
description: 公众号平台发布 adapter skill，用于从数据工作区 platforms/wechat/ 的平台稿生成本地预览、发布报告、Wenyan 输入，并在确认后上传公众号草稿箱。若用户意图是写一篇内容、继续一篇文章、从想法推进到预览/发布/复盘，优先进入 social-publishing-workflow；本 skill 只承接公众号发布准备和草稿箱写入，不负责完整社交内容流程编排。默认以 wenyan-mcp 作为发布底层，并把预览、报告、Wenyan 输入和非敏感发布结果管理在数据工作区 publishing/wechat/ 下。
---

# WeChat Draft

当用户要基于已有 `<workspacePath>/platforms/wechat/` 平台稿准备公众号文章、检查发布就绪状态、生成本地预览、准备 Wenyan 输入、上传公众号草稿箱，或维护公众号发布 adapter 时，使用本 skill。

本 skill 从写作和平台适配之后开始，不替代 `social-writing`，也不作为完整社交内容发布流程的入口；完整流程优先由 `social-publishing-workflow` 编排。

## 职责范围

首选底层是 [`wenyan-mcp`](references/wenyan-mcp.md)。除非用户明确选择其他底层，否则真实 Markdown 渲染、图片上传、凭证要求和草稿箱发布流程都由 `wenyan-mcp` 承担。

要做：

- 从 `<workspacePath>/platforms/wechat/` 读取平台就绪 Markdown。
- 在 `<workspacePath>/publishing/wechat/` 下生成本地预览产物。
- 预览和 Wenyan 准备阶段自动应用发布层排版与安全处理，但不修改人工写作源文件。
- 默认使用 `wenyan-mcp` 处理公众号渲染、图片上传和草稿创建。
- 底层配置遵循底层工具自己的文档要求。
- 本 skill 脚本只负责检查、报告和 Wenyan 输入生成。
- 用户文章发布产物和非敏感发布结果放在 `<workspacePath>/publishing/` 下。
- ArcSocial 项目根目录的 `arckit/` 只存放开源项目治理产物和平台契约，不存放个人文章发布产物。

不要做：

- 不把 `appsecret` 或 `access_token` 存入仓库。
- 除非上层有明确需要，不覆盖 `wenyan-mcp` 的凭证和配置约定。
- 不公开发布文章；公开发布要等未来 skill 明确扩展并增加门禁。
- 不把本地预览当作最终渲染结果；公众号编辑器仍可能标准化样式。
- 不把标准写作稿移出 `<workspacePath>/content/drafts/`，也不把平台稿移出 `<workspacePath>/platforms/wechat/`。
- 除非用户明确要求更新文章或元数据，不编辑 `<workspacePath>/content/` 或 `<workspacePath>/platforms/` 下的人工源文件。
- 预览或草稿准备阶段，不做未报告的内容级改写。

## 执行模式

默认选择能满足用户请求的最安全模式。

| 模式 | 远程写入 | 仓库写入 | 人工确认 |
|---|---:|---:|---|
| `check` | 否 | 否 | 否 |
| `prepare` | 否 | 只写 `<workspacePath>/publishing/wechat/` 下的生成文件 | 否，除非要改源文案 |
| `source-edit` | 否 | `<workspacePath>/platforms/wechat/` 或 `<workspacePath>/content/` | 是，除非用户已经明确要求编辑、更新或准备文案 |
| `draft` | 只创建公众号后台草稿 | 在 `<workspacePath>/publishing/wechat/` 记录结果摘要 | 是，必须先预览 |
| `publish` | 公开发布 | 结果摘要 | 本 skill 不支持 |

示例：

- “check this” -> `check`。
- “prepare this as a WeChat draft” -> `prepare`；只在 `<workspacePath>/publishing/wechat/` 生成产物，如果没有确认，不改源文案，也不远程写入。
- “create the WeChat draft now” -> `draft`；但必须已有预览产物，并且用户已经批准远程写入。

## 缺失项处理

可以不询问用户直接做：

- 运行 `doctor`、`preview --dry-run` 和本地校验命令。
- 生成或刷新 `<workspacePath>/publishing/wechat/*.full-preview.html`、`*.fallback-payload.json`、`*.report.md` 和 Wenyan-ready Markdown。
- 在生成的 `<workspacePath>/publishing/wechat/` 文件和报告中推导建议的 `title`、`digest` 或 Wenyan frontmatter。
- 检测缺失工具、缺失环境变量、缺失文章元数据、缺失封面配置。
- 当用户要求 agent 选择或生成封面时，在 `<workspacePath>/assets/wechat/covers/` 下生成或选择可发布质量的封面。必须使用真实图片生成流程或用户提供的资产；本 skill 不提供低质量兜底封面。
- 报告需要人工批准或执行的安装、配置命令。

必须询问或停止等待人工处理：

- 安装全局工具或包，包括 `npm install -g @wenyan-md/mcp`。
- 存储或输入凭证、API key、`WECHAT_APP_ID` 或 `WECHAT_APP_SECRET`。
- 编辑 `<workspacePath>/content/` 或 `<workspacePath>/platforms/` 下的人工源文件，除非用户明确要求这次编辑。
- 多个用户提供的封面都合理时，选择最终封面。如果用户要求 agent 生成或选择封面，agent 可以产出建议封面并继续，但远程建草稿前必须在 `*.full-preview.html` 中展示。
- 本地预览之后创建远程公众号草稿。用户之前明确要求，创建新草稿前必须先本地预览。
- 使用远程 Wenyan 服务/API key，或改变底层凭证行为。
- 公开发布。公开发布不在当前 skill 范围内。

## 目录契约

数据工作区发布文件：

```text
<workspacePath>/publishing/wechat/     公众号预览产物、payload 和非敏感日志。
<workspacePath>/platforms/wechat/      人工可编辑的公众号平台稿。
<workspacePath>/assets/wechat/         可选封面和正文图片源资产。
```

ArcSocial 项目根目录保留跨平台发布契约：

```text
arckit/publishing/_shared/
```

默认数据工作区是 `workspace/`。如果项目根目录存在 `arcsocial.config.json`，读取其中的 `workspacePath`。

只有本 skill 需要自身状态时，才使用用户级上层文件：

```text
~/.arckit/AgentWorkspace/social-ops/wechat/
```

`wenyan-mcp` 的凭证、API key、服务地址和环境变量遵循 `wenyan-mcp` 文档。仓库可以保存示例或 schema，但绝不保存真实 secret 或 token。

## 工作流

### 0. 启动前检查环境

任何草稿工作前，先运行：

```bash
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py doctor
```

检查：

- 本地 Wenyan 模式需要 Node.js 和 npm。
- 已安装 `wenyan-mcp`，或已配置远程 Wenyan MCP 服务。
- 本地模式要调用公众号 API 时，`WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 可用。
- 本地 API 调用需要处理公众号 IP 白名单。

如果本地缺少 `wenyan-mcp`，并且用户批准安装，运行：

```bash
npm install -g @wenyan-md/mcp
```

不要静默安装包。

快速失败规则：如果缺少 `wenyan-mcp`，且没有可用远程 Wenyan MCP 工具或服务，不要尝试真实建草稿。本轮结束时交付本地产物、缺失前提，以及下一步需要的命令或人工动作。

### 1. 确认源 Markdown

- 优先使用用户明确提供的路径。
- 否则使用 `<workspacePath>/platforms/wechat/YYYY-MM-DD-slug.md`。
- 如果只有 `<workspacePath>/content/drafts/YYYY-MM-DD-slug.md`，先通过写作流程适配到 `<workspacePath>/platforms/wechat/`。

### 2. 重新检查环境和文章就绪状态

```bash
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py doctor
```

用它提供上层判断：工具可用性、凭证环境、项目产物路径、缺失文章元数据，以及 `wenyan-mcp` 命令是否看起来已安装。

### 3. 生成项目内本地预览产物

需要预览时运行：

```bash
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py preview workspace/platforms/wechat/YYYY-MM-DD-slug.md
```

如果封面已经确定，显式传入。若已存在 `.wenyan.md`，且未传 `--cover`，`preview` 可以复用其中的 `cover` frontmatter。

```bash
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py preview workspace/platforms/wechat/YYYY-MM-DD-slug.md --cover workspace/assets/wechat/covers/YYYY-MM-DD-slug-cover.png
```

这不是最终 Wenyan 渲染。它写入：

```text
<workspacePath>/publishing/wechat/YYYY-MM-DD-slug.full-preview.html
<workspacePath>/publishing/wechat/YYYY-MM-DD-slug.fallback-payload.json
<workspacePath>/publishing/wechat/YYYY-MM-DD-slug.report.md
```

#### 自动发布风格处理

每次公众号预览和 Wenyan 准备都默认运行发布层风格处理。不要等用户明确说“参考最近发布文章”或“优化排版”才做。

这个处理必须：

- 查找 `<workspacePath>/publishing/wechat/*.wenyan-result.md` 下最近成功的公众号结果，映射回对应 `<workspacePath>/platforms/wechat/*.md`，并把它作为风格参考；
- 如果没有历史结果，回退到当前文章之外最近的 `<workspacePath>/platforms/wechat/*.md`；
- 保持 `<workspacePath>/content/` 和 `<workspacePath>/platforms/` 下的源文件不变；
- 应用确定性的发布安全转换，包括本地图片路径规范化和列表安全转换；
- 在 `*.report.md` 和 `*.full-preview.html` 中报告风格参考和内容变更范围。

默认只允许发布层变化：段落渲染、标题渲染、图片间距、列表安全、字段展示、预览和 Wenyan 就绪处理。只有 agent 明确执行公众号可读性优化时，才允许轻量编辑适配；这种适配必须体现在生成的预览/Wenyan 产物中，保留核心观点，不编造事实或经历，并清楚报告 `Content Change Scope`。如果改动会改变论证、增删核心观点或实质性重写文章，必须先停下询问。

使用 `*.full-preview.html` 让用户做草稿创建前的必要预览。它必须展示：

- 当前流程能提供哪些公众号/Wenyan 字段；
- 这篇文章实际填了哪些值；
- 已选封面；
- 摘要和本地渲染正文；
- 自动发布风格处理、风格参考和内容变更范围。

无写入验证使用：

```bash
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py preview workspace/platforms/wechat/YYYY-MM-DD-slug.md --dry-run
```

### 4. 生成 Wenyan-ready Markdown

准备草稿时，在 `<workspacePath>/publishing/wechat/` 下生成 Wenyan 输入：

```bash
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py prepare-wenyan workspace/platforms/wechat/YYYY-MM-DD-slug.md
```

它只写入一个生成文件：

```text
<workspacePath>/publishing/wechat/YYYY-MM-DD-slug.wenyan.md
```

脚本可以打印建议元数据，但不能把建议写回源文章，除非用户明确要求更新源文件。

当 `Publish Metadata` 包含 `Digest` 时，生成的 Wenyan Markdown 会在第一个 H1 后把摘要插入正文 blockquote；如果正文已有相同摘要，则不重复插入。这样在底层草稿 API 不单独暴露 digest 时，本地预览和公众号草稿正文仍保持一致。

如果需要封面，且用户要求 agent 生成封面，先走下面的封面质量流程，再准备 Wenyan 输入。

#### 封面质量流程

- 生成或使用可发布质量的 bitmap 封面，保存到 `<workspacePath>/assets/wechat/covers/YYYY-MM-DD-slug-cover.png`。
- 同 stem 保存图片生成 prompt、意图和有用 critique：`<workspacePath>/assets/wechat/covers/YYYY-MM-DD-slug-cover.prompt.md`。
- 封面应针对文章主题，缩略图中也能快速看懂，避免在公众号列表里不可读的小字。
- 根据文章标题、摘要和核心隐喻设计干净的编辑型画面方向，避免通用抽象填充。
- 在同 stem sidecar 中保留 prompt 或 rationale，方便 `preview` 纳入报告和完整预览。不要保存 secret、私人身份细节或外部凭证。
- 如果无法生成图片，且用户没有提供封面，远程建草稿前必须停止并报告缺少封面资产。

封面存在后，建草稿前必须带封面重新预览：

```bash
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py preview workspace/platforms/wechat/YYYY-MM-DD-slug.md --cover workspace/assets/wechat/covers/YYYY-MM-DD-slug-cover.png
python3 .agents/skills/wechat-draft/scripts/wechat_draft.py prepare-wenyan workspace/platforms/wechat/YYYY-MM-DD-slug.md --cover workspace/assets/wechat/covers/YYYY-MM-DD-slug-cover.png
```

重要路径规则：Wenyan 解析相对 `cover` 和图片路径时，以生成的 `.wenyan.md` 文件所在目录为基准。如果图片在数据工作区 `assets/` 下，`<workspacePath>/publishing/wechat/` 下的生成文件必须使用类似路径：

```yaml
cover: "../../../assets/images/example.png"
```

#### 正文图片流程

- 生成的正文图片放在 `<workspacePath>/assets/wechat/body/`。
- 每张图片的 prompt 或 rationale 保存为同 stem sidecar，例如 `<workspacePath>/assets/wechat/body/YYYY-MM-DD-slug-01.prompt.md`。
- `<workspacePath>/platforms/wechat/*.md` 可以用数据工作区根路径（`assets/wechat/body/example.png`）或源文件相对路径引用图片。预览脚本会在生成产物中改写本地图片路径，让本地预览和 Wenyan 输入都能从 `<workspacePath>/publishing/wechat/` 正确解析。
- 正文图片要克制使用。它们应提供节奏或解释某一节，不要重复封面，也不要引入私人家庭细节，除非用户明确批准。

#### 公众号列表安全

- 不要在 `<workspacePath>/platforms/wechat/*.md` 中手写 `<ul>` / `<li>`；公众号草稿渲染可能产生空白列表项。
- 普通列表需要显式公众号安全样式时，使用段落 bullets，例如 `<p style="margin: 0 0 8px; line-height: 1.75; color: #334155;">• Item</p>`。
- 预览和 Wenyan 准备脚本会把 Markdown `- item` / `* item` 列表和简单 HTML `<ul><li>` 列表转换成段落 bullets。
- 远程建草稿前，如果仍有 `<ul>` / `<li>` 警告，视为发布风险并修复平台稿。

### 5. 检查并报告预览产物

- 确认仓库能提供的文章元数据。
- 确认 `*.full-preview.html` 包含 API/Wenyan 字段矩阵和已选封面。
- 确认自动发布风格处理已运行。
- 确认使用了哪篇最近公众号文章作为风格参考；如果没有找到，要说明。
- 确认发布层处理没有修改源文件。
- 确认本地 fallback `content` 是否能转换成 HTML。
- 明确指出缺失封面、缺失摘要、字段过长、未解析本地图片或不稳定列表标记。
- 生成图片 sidecar 存在时，确认图片生成说明已纳入报告。

### 6. 使用 `wenyan-mcp` 做真实草稿箱写入

- 如果当前工具列表中有 `wenyan-mcp` MCP 工具，优先使用它。
- 如果只有本地命令可用，按 `wenyan-mcp` 文档调用和配置。
- Codex 会话中新配置的 MCP 工具有时不会热加载，这时使用 `node tools/scripts/wenyan-mcp-call.mjs`；它读取 `~/.codex/config.toml` 中的 `[mcp_servers.wenyan]`，把配置的 env/args 传给 `wenyan-mcp`，并且不打印 secret。
- 让 Wenyan 处理最终渲染、图片上传、封面处理和公众号草稿创建。
- 把非敏感结果摘要记录到 `<workspacePath>/publishing/wechat/`。
- 远程建草稿调用之前必须立即停下请求确认，除非用户在当前回合已经明确批准这次远程写入。
- 如果缺少凭证或 Wenyan 运行时，立即停止并报告前置条件，不尝试 fallback 路径。

辅助调用：

```bash
node tools/scripts/wenyan-mcp-call.mjs tools/call publish_article '{"file":"workspace/publishing/wechat/YYYY-MM-DD-slug.wenyan.md","theme_id":"default"}'
```

## Markdown 输入约定

脚本理解当前 `<workspacePath>/platforms/wechat/` 格式，以及这些可选字段：

```markdown
## Publish Metadata

- Title: Article title
- Author: Author name
- Digest: Short summary
- Cover media ID: WECHAT_THUMB_MEDIA_ID
- Show cover: 0
- Need open comment: 0
- Only fans can comment: 0
- Content source URL:
```

字段缺失时，脚本使用保守默认值，并在报告中记录 warning。

正文来自 `## Adapted Copy`。如果 `Publish Metadata` 缺少 `Title`，该 section 中第一个 `# Heading` 会成为标题。

## 必要配置指引

底层配置优先遵循 `wenyan-mcp`。常见要求包括：

- 本地安装 `wenyan-mcp`，或配置远程 Wenyan 服务。
- 本地模式需要环境变量中的 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`，或者服务/API-key 设置。
- 本地模式直接调用公众号官方 API 时，需要公众号 IP 白名单。
- Wenyan-ready Markdown frontmatter。Wenyan 文档中 `title` 至少是必需字段；可选字段包括 `cover`、`author`、`source_url`、`type`、`image_list`、`need_open_comment` 和 `only_fans_can_comment`。

上层文章就绪状态，引导用户检查：

- `Title`：文章必需。
- `Digest`：建议提供，不要依赖公众号默认摘要。
- `Cover`：如果使用 Wenyan 封面处理，需要本地路径或远程 URL。
- `Adapted Copy`：Wenyan 将渲染和上传的正文。

用户询问缺什么，或真实 API 调用因为配置不完整失败时，使用 `doctor`。如果 `doctor` 和 `wenyan-mcp` 结论冲突，以 `wenyan-mcp` 作为底层要求的权威来源。

## 封面质量门禁

只有满足这些条件，封面才算可用于远程建草稿：

- 已存在于 `<workspacePath>/assets/wechat/covers/` 或其他用户明确批准的路径；
- `*.full-preview.html` 同时展示封面、实际标题、摘要和正文；
- 报告记录了传给 Wenyan 的实际 `cover` 值；
- 如果存在同 stem 图片 prompt sidecar，报告已记录；
- 封面来自真实图片生成流程或用户批准的源资产。

元数据缺失时，先在 `<workspacePath>/publishing/wechat/` 或最终报告中生成建议。不要把建议的 `Digest`、`Cover` 或文案改动写入 `<workspacePath>/platforms/wechat/*.md`，除非用户明确要求更新源文件。

对 Wenyan 来说，`cover` 或至少一张正文图片在操作上是必需的。`thumb_media_id` 属于 fallback 直连公众号 API payload，不是准备 Wenyan 输入的首选方式。

## 扩展规则

保持平台中立概念分离：

```text
source Markdown -> platform adaptation -> rendered content -> publish payload -> publish result
```

新增其他平台时，在 `<workspacePath>/publishing/<platform>/` 下新增 adapter 产物目录；不要把其他平台行为硬编码进公众号脚本。

## 输出契约

使用本 skill 后，汇报：

- `source`: 输入 Markdown 路径。
- `full_preview_html`: 生成的字段与视觉预览路径，如果已创建。
- `payload_json`: 生成的 API payload 路径，如果已创建。
- `fallback_payload_json`: 生成的 fallback 字段预览 payload 路径，如果已创建。
- `report`: 生成的校验报告路径，如果已创建。
- `draft_result`: 公众号草稿结果路径，如果已创建。
- `wenyan_result`: Wenyan MCP 响应摘要路径，如果已创建。
- `needs_manual_review`: yes。
- `next_step`: 浏览器预览、配置凭证、创建草稿，或去公众号后台检查。
