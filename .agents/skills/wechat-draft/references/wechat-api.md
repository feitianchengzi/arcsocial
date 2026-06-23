# WeChat Official Account Draft API Notes

This reference captures the API shape used by the local `wechat_draft.py` fallback helper. The preferred foundation for real draft creation is `wenyan-mcp`; recheck the official WeChat documentation before broadening fallback behavior.

## Access Token

Endpoint:

```text
GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET
```

The fallback helper caches `access_token` in the user-level AgentWorkspace directory with an expiry timestamp. `wenyan-mcp` may use its own credential and token behavior; treat its documentation as authoritative when it is the active foundation. Do not store tokens in the repository.

## Add Draft

Endpoint:

```text
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN
```

Payload:

```json
{
  "articles": [
    {
      "article_type": "news",
      "title": "",
      "author": "",
      "digest": "",
      "content": "",
      "content_source_url": "",
      "thumb_media_id": "",
      "show_cover_pic": 0,
      "need_open_comment": 0,
      "only_fans_can_comment": 0
    }
  ]
}
```

Important constraints:

- `content` is HTML, not Markdown.
- `thumb_media_id` should be a WeChat permanent image material media id.
- Images inside `content` should use WeChat-hosted image URLs returned by the relevant image upload API. External image URLs may be filtered.
- JavaScript, iframe content, external CSS, and complex unsupported markup should not be relied on.
- The draft API creates a backend draft; it does not publish the article.

## Future Work

Likely fallback-helper future commands:

- Upload cover image as permanent material and write back `Cover media ID`.
- Upload body images and replace local paths with WeChat image URLs.
- Query draft status and update local result metadata.
- Optional gated publish command after manual review.
