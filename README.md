# ArcSocial

ArcSocial 是一个面向 Agent 协作的开源社交内容工作区。它不是 Web/App 服务，不需要启动常驻服务；用户拉取本项目后，直接在 ArcSocial 项目根目录中和 agent 协作完成选题、写作、平台适配、预览和发布准备。

ArcSocial 项目本体只放可复用能力：Agent Skills、发布流程、检查脚本、模板和平台 adapter。用户自己的文章、素材、平台稿、发布记录和指标数据放在独立的数据工作区，默认挂载到 `workspace/`。

英文说明见 [README.en.md](README.en.md)。

## 当前支持

- 通用写作流程：支持从原始想法生成标准草稿，再生成不同平台的适配稿。
- 微信公众号：当前已有完整 adapter，支持本地检查、预览、Wenyan 输入生成，并在确认后写入公众号草稿箱。
- 其他社交平台：当前可生成平台适配稿；如果没有对应 adapter，ArcSocial 会停在“平台稿就绪”，不会假装支持远程发布。

微信公众号草稿箱能力使用开源项目 [`wenyan-mcp`](https://github.com/caol64/wenyan-mcp) 作为底层。安装方式、`WECHAT_APP_ID` / `WECHAT_APP_SECRET` 配置、IP 白名单、本地模式和 Server 模式，请参考它的官方 README。ArcSocial 不保存真实 secret 或 access token。

## 首次初始化

先准备个人数据工作区。推荐把任意个人内容 Git 仓库作为 submodule 挂载到 ArcSocial 根目录：

```bash
node tools/scripts/init-workspace.mjs --repo <your-content-repo-url> --path workspace
node tools/scripts/doctor.mjs
```

如果你还没有个人数据仓库，可以先用模板初始化一个本地工作区：

```bash
node tools/scripts/init-workspace.mjs --new --path workspace
node tools/scripts/doctor.mjs
```

默认工作区路径来自 `arcsocial.config.json`：

```json
{
  "workspacePath": "workspace"
}
```

如果你把工作区改成其他路径，`init-workspace.mjs --path` 和 `arcsocial.config.json` 应保持一致。

## 社交平台配置

初始化后先运行 `doctor`。它会检查工作区边界、关键目录、`wenyan-mcp`、`WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`。

微信公众号配置遵循 `wenyan-mcp` 官方文档。通常需要准备：

- `wenyan-mcp`。
- `WECHAT_APP_ID`。
- `WECHAT_APP_SECRET`。
- 公众号后台 IP 白名单。

不要把 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`、`appsecret` 或 `access_token` 提交到 Git 仓库。

## 日常如何使用

用户不需要先理解所有目录。你可以直接告诉 agent 你要做什么内容、发到哪个平台、现在处在哪一步。Agent 会按 ArcSocial 流程创建草稿、生成平台稿、准备预览，并在需要你确认时停下来。

可以这样开始：

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

## 项目边界

这个仓库是 ArcSocial 开源项目本体。

- `.agents/skills/` 存放可复用的 Agent Skills。
- `arckit/` 存放本开源项目自己的 ArcKit 治理产物和项目记忆，属于开源项目本身，不是用户内容数据。
- `docs/`、`playbooks/`、`skills/`、`tools/` 记录并支撑可复用工作流。
- `templates/workspace/` 是给用户初始化个人内容数据仓库的干净模板。
- `workspace/` 是推荐的个人数据挂载位置，通常作为 Git submodule 存在；它不属于 ArcSocial 开源项目本体。

用户自己的文章、草稿、平台适配稿、发布素材、指标和私有平台数据，应该放在任意独立 Git 仓库中，并作为 submodule 挂载到 ArcSocial 项目下。这个数据仓库可以使用 `templates/workspace/` 初始化，也可以是已有仓库，只要目录结构满足 ArcSocial 的读写约定即可。

## 目录结构

```text
.agents/               社交内容发布流程的可复用 Agent Skills。
arckit/                本开源项目的 ArcKit 项目产物。
docs/                  面向用户和贡献者的文档。
playbooks/             可复用流程、提示词、检查清单和实验记录。
skills/                后续可移植的 skill/package 材料。
tools/                 脚本、应用和工具配置。
templates/workspace/   给用户使用的干净内容工作区模板。
workspace/             推荐的个人数据 submodule 挂载位置，不提交到开源项目。
```

`workspace/` 内部目录只作为 agent 读写契约。通常用户不用手动记住它们；需要排查或手动维护时再查看 `templates/workspace/`。

## 文件命名

内容文件使用日期前缀：

```text
YYYY-MM-DD-topic.md
```
