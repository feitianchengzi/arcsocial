# 用户偏好沉淀

本 reference 用于把用户反馈分流到正确位置，避免把个人审美、表达口吻或一次性文章修改写死进通用 skill。

## 核心原则

- 通用 skill 固化流程能力、判断方法、发布门禁、平台约束和安全边界。
- 用户偏好记录个人长期稳定的写作口吻、标题力度、排版审美、视觉风格、固定结尾和平台习惯。
- 当前文章修改只作用于当前内容对象，不自动提升为长期偏好。
- 只有多次出现、用户明确要求长期沿用，或明显会影响后续同类发布的反馈，才建议写入用户偏好。

## 偏好文件位置

偏好文件属于用户数据，默认写入数据工作区：

```text
<workspacePath>/preferences/
  user-profile.md
  writing-style.md
  title-style.md
  wechat-style.md
  visual-style.md
  reusable-blocks.md
```

如果文件不存在，不要阻塞当前任务；按通用规则继续，并在最终汇报中说明可选偏好沉淀建议。

## 归因分类

处理用户反馈时，先归为下面一种：

- `workflow_capability`：流程缺陷，例如缺少标题校准、没有预览门禁、改图后没有重新发布草稿。
- `platform_rule`：平台适配规则，例如公众号标题长度、封面裁切、列表安全、图片消息结构。
- `user_preference`：用户长期偏好，例如语言克制、少营销腔、封面无文字、视觉不要花哨。
- `current_article_edit`：当前文章的一次性修改，例如某个段落太长、某张图文字不准、某个标题不够精准。
- `product_gap`：当前能力不能稳定支持的功能缺口，例如偏好 UI、跨平台偏好 profile、自动偏好候选合并。

## 写入边界

- `workflow_capability` 和 `platform_rule` 可以建议维护对应 skill、脚本或平台 adapter。
- `user_preference` 只能写入 `<workspacePath>/preferences/`，不能直接写成通用 skill 硬规则。
- `current_article_edit` 只改当前草稿、平台稿、预览产物或图片资产。
- `product_gap` 记录为后续产品缺口，不假装已经实现。
- 写入或更新偏好文件前，除非用户已经明确要求“沉淀偏好”“以后都这样”，否则先报告建议并等待确认。

## 读取规则

- 写作和标题任务优先读取 `writing-style.md`、`title-style.md` 和 `reusable-blocks.md`。
- 公众号平台适配和预览优先读取 `wechat-style.md`、`visual-style.md` 和 `reusable-blocks.md`。
- 封面、正文插图、关注图等图片任务优先读取 `visual-style.md`。
- 多个偏好冲突时，当前用户明确指令优先，其次是当前平台偏好，再其次是通用用户偏好。

## 汇报要求

涉及用户反馈归因时，最终汇报包含：

- `feedback_classification`: 本轮反馈归因。
- `skill_update_needed`: 是否需要维护通用 skill 或平台 adapter。
- `preference_update_suggested`: 是否建议写入用户偏好。
- `preference_paths`: 涉及的偏好文件路径。
- `current_article_only`: 哪些修改只作用于当前文章。
