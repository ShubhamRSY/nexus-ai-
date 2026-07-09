package com.nexus.chat

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

/** Minimal Nexus chat client for Android. */
class NexusChat(
    private val apiBase: String,
    private var token: String,
    private val sessionId: String = "android-${System.currentTimeMillis()}",
) {
    private val client = OkHttpClient()
    private val json = "application/json; charset=utf-8".toMediaType()

    fun send(message: String): String {
        val body = JSONObject()
            .put("message", message)
            .put("session_id", sessionId)
            .put("agent_id", "chat_support")
            .toString()
            .toRequestBody(json)
        val req = Request.Builder()
            .url("$apiBase/chat")
            .addHeader("Authorization", "Bearer $token")
            .post(body)
            .build()
        client.newCall(req).execute().use { resp ->
            val obj = JSONObject(resp.body?.string() ?: "{}")
            return obj.optString("response", obj.optString("detail", ""))
        }
    }
}
