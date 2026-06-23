---
name: arcsocial-intro
description: ArcSocial 新用户入口 skill。当用户询问“这个项目怎么用”“开始使用 ArcSocial”“初始化工作区”“支持哪些平台”“如何配置公众号/社交平台”“我该怎么跟 agent 对话”或需要项目自我介绍时使用。负责用产品视角介绍 ArcSocial、检查初始化状态、说明社交平台配置边界，并把用户引导到第一条可执行对话。
---

# ArcSocial Intro

本 skill 是 ArcSocial 面向新用户的默认自我介绍和启动引导。它不负责写文章或发布文章；当用户准备正式推进一篇内容时，交给 `social-publishing-workflow`。

## 必须讲清楚的重点

介绍 ArcSocial 时，优先讲用户真正需要知道的三件事：

1. ArcSocial 是什么。
2. 当前支持哪些社交平台。
3. 用户下一步该如何初始化并开始和 agent 对话。

不要把目录结构当成主说明。目录只在初始化、故障排查或用户追问时展开。

## 项目定位

ArcSocial 是一个面向 Agent 协作的开源社交内容工作区。它不是 Web/App 服务，不需要启动常驻服务。用户拉取 ArcSocial 后，直接在项目根目录里和 agent 协作：

- ArcSocial 项目本体提供 agent skills、发布流程、检查脚本、模板和平台 adapter。
- 用户自己的文章、素材、平台稿、发布记录和指标数据放在数据工作区。
- 默认数据工作区是 `workspace/`；可通过 `arcsocial.config.json` 的 `workspacePath` 修改。
- 推荐把 `workspace/` 配置成用户自己的 Git 仓库 submodule，支持任意 Git 仓库。

## 当前平台支持

对外说明平台支持时使用这个口径：

- 通用写作流程：支持从想法到标准草稿，再到平台适配稿。
- 微信公众号：当前已有完整 adapter，支持本地检查、预览、Wenyan 输入生成，并在确认后写入公众号草稿箱。
- 其他社交平台：当前可生成平台适配稿；如果没有对应 adapter，停在“平台稿就绪”，不假装已经支持远程发布。

微信公众号底层使用开源项目 `wenyan-mcp`。`WECHAT_APP_ID`、`WECHAT_APP_SECRET`、IP 白名单、本地模式和 Server 模式都遵循 `wenyan-mcp` 官方文档。ArcSocial 不保存真实 secret 或 access token。

## 初始化引导

介绍首次使用时，先引导用户做两类准备。

### 1. 工作区准备

如果用户已有个人内容 Git 仓库：

```bash
node tools/scripts/init-workspace.mjs --repo <your-content-repo-url> --path workspace
node tools/scripts/doctor.mjs
```

如果用户还没有个人内容仓库：

```bash
node tools/scripts/init-workspace.mjs --new --path workspace
node tools/scripts/doctor.mjs
```

如果用户修改了 `arcsocial.config.json` 的 `workspacePath`，命令中的 `--path` 应与配置保持一致。

### 2. 社交平台准备

总是先运行：

```bash
node tools/scripts/doctor.mjs
```

医生脚本会检查：

- `workspacePath` 是否存在。
- 工作区关键目录是否满足读写契约。
- `wenyan-mcp` 是否安装。
- `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 是否可用。

如果用户要使用微信公众号，告诉用户按 `wenyan-mcp` 官方 README 配置公众号凭证和 IP 白名单。不要要求用户把 secret 写入仓库。

## 日常使用引导

用户不需要先理解所有文档目录。给用户的默认说法是：

> 你可以直接告诉我你要做什么内容、发到哪个平台、现在处在哪一步。我会按 ArcSocial 流程创建草稿、生成平台稿、准备预览，并在需要你确认时停下来。

给出可直接复制的对话示例：

```text
用 ArcSocial 帮我把这个想法整理成一篇公众号文章：……
```

```text
继续完善 workspace/content/drafts/2026-06-23-example.md，准备发公众号。
```

```text
检查这篇公众号稿能不能发布，并生成本地预览。
```

```text
把这篇标准草稿适配成 X 和公众号两个版本。
```

如果 `doctor` 未通过，先引导修复初始化或平台配置，不进入正式写作/发布流程。

## 交接规则

- 用户问项目是什么、怎么开始、怎么配置、支持哪些平台：留在本 skill。
- 用户给出内容想法并要求写作、整理、适配、预览或发布：交给 `social-publishing-workflow`。
- 用户只要求生成或修改草稿：可由 `social-publishing-workflow` 调用 `social-writing`。
- 用户已有公众号平台稿并要求预览、Wenyan 准备或创建草稿箱：可由 `social-publishing-workflow` 调用 `wechat-draft`。

## 输出格式

面向新用户的回答保持短而可执行：

- 先用 2-4 句话说明 ArcSocial 是什么和当前平台支持。
- 再给初始化命令。
- 再给社交平台配置说明。
- 最后给 2-4 个“你可以这样跟我说”的例子。

如果发现项目未初始化，明确说当前阻塞在 `workspace/` 或平台配置，并给下一条命令。
