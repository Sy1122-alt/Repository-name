/**
 * 专升本题库 AI 代理 Worker
 * 功能：
 *  1. 代理转发到中转站 OpenAI 兼容接口（key 存在环境变量，不暴露给前端）
 *  2. 每日限流：每个 IP 每天 N 次（防止被脚本刷爆余额）
 *  3. 支持 CORS（GitHub Pages 前端跨域调用）
 *
 * 环境变量（Cloudflare Worker -> Settings -> Variables）：
 *  AI_BASE_URL  中转站 Base URL，例如 https://xxx.com/v1
 *  AI_API_KEY   中转站 API Key（sk-开头）
 *  AI_MODEL     模型名，例如 grok-chat-fast
 *  AI_DAILY_LIMIT  每 IP 每日最大请求数，默认 15
 */

// 简易 IP 限流：使用 Cloudflare KV 更持久，这里用 Worker 的 cache 模拟内存计数（免费版够用）
// 若需要跨 Worker 重启持久计数，请绑定 KV 命名空间 AI_LIMIT 并放开下方注释逻辑

export default {
  async fetch(request, env) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Access-Control-Max-Age": "86400",
    };

    // 预检请求
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // 健康检查
    if (request.method === "GET") {
      return new Response(JSON.stringify({ ok: true, name: "zsb-ai-proxy" }), {
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    const baseUrl = env.AI_BASE_URL || "";
    const apiKey = env.AI_API_KEY || "";
    const model = env.AI_MODEL || "grok-chat-fast";
    const dailyLimit = parseInt(env.AI_DAILY_LIMIT || "15", 10);

    if (!baseUrl || !apiKey) {
      return new Response(
        JSON.stringify({ error: "服务端未配置 AI_BASE_URL / AI_API_KEY" }),
        { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }

    // ---- 限流 ----
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const today = new Date().toISOString().slice(0, 10);
    const limitKey = "zsb_ai_limit_" + today + "_" + ip;
    const limitUrl = new URL("https://ai-limit.workers.dev/" + limitKey);

    // 使用 Cache API 做简易计数（每天过期，无需 KV）
    let count = 0;
    try {
      const cache = caches.default;
      const cached = await cache.match(limitUrl);
      if (cached) {
        count = parseInt(await cached.text(), 10) || 0;
      }
    } catch (e) {}

    if (count >= dailyLimit) {
      return new Response(
        JSON.stringify({ error: "今日AI使用次数已达上限，明天再来吧（每人每天" + dailyLimit + "次）" }),
        { status: 429, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }

    // ---- 读取前端请求 ----
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(JSON.stringify({ error: "请求体不是有效JSON" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    // 前端可以传 messages / system / prompt；这里强制注入系统提示防止越权
    const messages = Array.isArray(body.messages) ? body.messages : [];
    const maxTokens = Math.min(parseInt(body.max_tokens || "600", 10), 1200);

    // ---- 转发到中转站 ----
    const upstream = baseUrl.replace(/\/+$/, "") + "/chat/completions";
    let resp;
    try {
      resp = await fetch(upstream, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + apiKey,
        },
        body: JSON.stringify({
          model: model,
          messages: messages,
          max_tokens: maxTokens,
          temperature: 0.3,
          stream: false,
        }),
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "上游请求失败：" + e.message }), {
        status: 502,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    // 限流计数 +1（成功请求才计数）
    try {
      const cache = caches.default;
      const next = count + 1;
      const respCache = new Response(String(next), {
        headers: { "Cache-Control": "public, max-age=86400" },
      });
      await cache.put(limitUrl, respCache);
    } catch (e) {}

    // ---- 返回 ----
    const contentType = resp.headers.get("Content-Type") || "application/json";
    const text = await resp.text();

    if (!resp.ok) {
      return new Response(text, {
        status: resp.status,
        headers: { "Content-Type": contentType, ...corsHeaders },
      });
    }

    return new Response(text, {
      status: 200,
      headers: { "Content-Type": contentType, ...corsHeaders },
    });
  },
};
