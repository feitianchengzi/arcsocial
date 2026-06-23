# ArcSocial

ArcSocial 是一个面向 Agent 协作的开源社交内容发布工作区。用户拉取本项目后，直接在 ArcSocial 项目根目录中工作；个人文章、素材、平台稿和指标数据通过 Git submodule 挂载到项目内的数据工作区。

英文说明见 [README.en.md](README.en.md)。

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

## 初始化个人数据工作区

推荐方式是在 ArcSocial 根目录下把任意个人数据仓库挂载为 submodule：

```bash
node tools/scripts/init-workspace.mjs --repo <your-content-repo-url> --path workspace
```

如果你还没有个人数据仓库，可以先用 `templates/workspace/` 创建一个新的 Git 仓库，再把它作为 submodule 挂载回来。

```bash
node tools/scripts/init-workspace.mjs --new --path workspace
```

ArcSocial 后续的写作、适配、预览和发布流程都应该读写 `workspace/` 下的数据，而不是把个人内容写入开源项目根目录。

初始化后运行检查：

```bash
node tools/scripts/doctor.mjs
```

## 内容工作流

在 `workspace/` 数据仓库中：

1. 在 `inbox/` 捕获原始想法、参考资料和素材。
2. 把值得推进的内容移动到 `content/drafts/`，使用 `content/drafts/_template.md` 建立标准草稿。
3. 在 `platforms/` 下为不同平台生成适配稿。
4. 把准备发布的内容移动到 `content/ready/`。
5. 发布后，把最终版本归档到 `content/published/`。
6. 在 `publishing/` 保存平台预览、发布准备产物和非敏感结果记录。
7. 在 `data/metrics/` 和 `playbooks/experiments/` 记录数据、反馈和复盘。

## 微信公众号发布

微信公众号草稿箱创建使用开源项目 [`wenyan-mcp`](https://github.com/caol64/wenyan-mcp) 作为底层。安装方式、`WECHAT_APP_ID` / `WECHAT_APP_SECRET` 配置、IP 白名单、本地模式和 Server 模式，请参考它的官方 README。

`workspace/` 可以保存文章源文件、预览产物和非敏感发布记录。不要提交 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`、`appsecret` 或 `access_token`。

## 命名规则

内容文件使用日期前缀：

```text
YYYY-MM-DD-topic.md
```

示例：

```text
2026-05-24-agent-workflow.md
2026-05-24-agent-workflow-x.md
2026-05-24-agent-workflow-wechat.md
```

## 运营规则

- `inbox/` 可以保持粗糙，其他目录应尽量有明确意图。
- `content/drafts/` 存放平台适配前的标准内容来源。
- `platforms/` 存放平台特定的文案、结构和约束。
- `assets/` 存放源素材和可复用媒体，不存最终发布正文。
- `publishing/` 存放平台发布准备产物和非敏感结果记录。
- `playbooks/` 记录可复用方法；`skills/` 存放可执行或半结构化能力。
- `data/` 用于计划和指标，不作为原始创作笔记库。
