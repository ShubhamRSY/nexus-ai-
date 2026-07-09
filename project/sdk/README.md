# Nexus Mobile & Embed SDK

Lightweight clients for iOS, Android, and web embed.

## Web embed (chat widget)

```html
<script src="https://yournexus.duckdns.org/static/nexus-widget.js"></script>
<script>
  NexusChat.init({
    apiBase: 'https://yournexus.duckdns.org/api/v1',
    token: 'YOUR_JWT',  // from /auth/login or /auth/demo-login
    sessionId: 'mobile-session-1',
    position: 'bottom-right',
  });
</script>
```

## REST API (all platforms)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Get JWT |
| `/auth/demo-login` | POST | Sandbox JWT |
| `/chat` | POST | Send message |
| `/chat/stream` | WebSocket | Streaming chat |
| `/portal/kb/search` | POST | KB search (no auth) |
| `/portal/tickets` | POST | Create ticket |

## iOS (Swift)

See `ios/NexusChat.swift` — URLSession wrapper around `/chat`.

## Android (Kotlin)

See `android/NexusChat.kt` — OkHttp wrapper around `/chat`.

## React Native

Use the web widget in a `WebView`, or call REST directly with the same JSON body as `/chat`.
