---
name: social-writing
description: 社交内容流程中的底层写作 skill，用于记录原始输入、澄清缺失上下文、生成可长期维护的 Markdown 标准草稿，并在上层流程或用户明确要求时产出平台适配稿。若用户意图是推进一篇内容从想法到预览、发布或复盘，优先进入 social-publishing-workflow；本 skill 只承接写作和平台稿生成，不负责完整发布编排。
---

# Social Writing

当用户要把想法、口述式材料、粗糙段落或讨论内容变成社交媒体内容，且任务重点是记录、成稿或平台稿生成时，使用本 skill。若用户正在推进完整发布流程，先由 `social-publishing-workflow` 编排，再按阶段调用本 skill。

本 skill 负责早期写作流程：

1. 保留原始输入。
2. 判断是否需要澄清。
3. 创建或更新标准草稿。
4. 只有用户要求具体平台时，才做平台适配。

## 数据写入位置

ArcSocial 项目根目录只存放开源项目能力和治理产物。所有用户内容数据都写入数据工作区。

默认数据工作区是 `workspace/`。如果项目根目录存在 `arcsocial.config.json`，读取其中的 `workspacePath` 作为数据工作区路径。

文件写入这些位置：

```text
<workspacePath>/inbox/ideas/       原始输入和快速记录。
<workspacePath>/content/drafts/    可长期维护的标准草稿。
<workspacePath>/platforms/         用户要求具体平台时生成的平台适配稿。
```

不要把用户文章、草稿、平台稿或素材写到 ArcSocial 项目根目录的 `inbox/`、`content/`、`platforms/`、`assets/` 或 `data/`。

文件名使用日期开头：

```text
YYYY-MM-DD-short-slug.md
```

如果用户没有给标题，根据核心想法生成简短 slug。

## 默认流程

### 1. 记录原始输入

重写之前，必须先保留用户原始表达。

当用户提供新的想法、笔记、粗糙段落、口述式材料或未结构化写作输入时，在 `<workspacePath>/inbox/ideas/` 下创建原始记录。

使用这个格式：

```markdown
# Short Title

## Status

- State: captured
- Created: YYYY-MM-DD
- Source: user input

## Raw Input

Original user wording goes here.

## Initial Read

- Core idea:
- Possible audience:
- Possible angle:
- Missing context:

## Next Step

clarify | draft | park
```

`Raw Input` 中必须尽量保留用户原话。轻微清理只能发生在其他区域。

### 2. 判断是否需要澄清

只有缺失信息会实质影响成稿方向时，才问最多 3 个简短问题。

以下情况需要澄清：

- 受众不明确。
- 当前必须知道目标平台或内容形式。
- 输入中存在多个可能角度，直接选择会过于武断。
- 核心判断依赖缺失的事实、引用或例子。

如果用户明显只是想快速记录，不要追问；记录下来，并把 `Next Step` 设为 `clarify`。

### 3. 创建标准草稿

上下文足够时，在 `<workspacePath>/content/drafts/` 下创建草稿。

除非仓库已有更具体模板，否则使用这个格式：

```markdown
# Title

## Status

- Stage: draft
- Created: YYYY-MM-DD
- Source: ../relative/path/to/raw-capture.md

## Core Idea

One clear sentence describing the point.

## Audience

Who this is for.

## Angle

Why this is worth reading.

## Draft

The canonical version before platform adaptation.

## Supporting Material

- References:
- Assets:
- Examples:
- Data:

## Open Questions

- Question or gap that should be resolved before publishing.

## Platform Notes

- X:
- LinkedIn:
- WeChat:
- Xiaohongshu:
- Zhihu:
```

如果原始记录已经存在，更新其中的草稿路径，不要重复复制原始输入。

### 4. 平台适配

只有用户要求适配、发布或准备某个明确平台时，才创建平台文件。

路径使用：

```text
<workspacePath>/platforms/<platform>/YYYY-MM-DD-short-slug.md
```

`<workspacePath>/content/drafts/` 是标准来源；不要让平台稿成为唯一事实来源。

公众号适配规则：

- 人工可编辑的平台稿写到 `<workspacePath>/platforms/wechat/`。
- 不把这个文件当作最终渲染形态。
- 如果用户要发公众号图片消息/小绿书，在 `## Publish Metadata` 中写 `- Type: image`，并在正文放图片或填写 `- Image List: path1, path2`。
- 当用户要求本地预览、草稿箱准备或发布时，交给 `wechat-draft`；它会在 `<workspacePath>/publishing/wechat/` 下生成预览和 Wenyan 产物，并自动应用发布层排版与安全处理。
- 不在本 skill 中重复处理公众号预览职责，包括选择最近已发布文章作为风格参考、生成 Wenyan 输入、列表安全转换、最终本地预览。
- 如果做公众号适配时进行了内容层面的调整，必须明确说明，并确保标准草稿仍可追溯。

## 行为规则

- 优先生成一个小而有用的文件，不要提出流程负担很重的问题。
- 保证用户原始输入可恢复。
- 区分记录、标准草稿和平台适配。
- 不编造个人经历、数据、引用或外部事实。
- 不确定的判断写入开放问题。
- 用户说“先记一下”时，只创建 inbox 记录。
- 用户说“整理成内容”时，在条件允许时同时创建原始记录和标准草稿。
- 用户指定平台时，在上下文足够的情况下创建原始记录、标准草稿和平台适配稿。

## 输出契约

写入文件后，汇报：

- `raw`: 创建或更新的原始记录路径。
- `draft`: 创建或更新的标准草稿路径。
- `platform`: 创建或更新的平台适配稿路径。
- `needs_clarification`: yes 或 no。
- `next_step`: 建议的下一步。
