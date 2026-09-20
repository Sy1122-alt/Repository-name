/**
 * 专升本题库 AI 代理 + 题目投稿 Worker
 * 功能：
 *  1. AI：代理转发到中转站 OpenAI 兼容接口（key 存在环境变量，不暴露给前端）
 *  2. AI 每日限流：每个 IP 每天 N 次（防止被脚本刷爆余额）
 *  3. 投稿：POST /api/submit 存 KV；GET /api/list?key=xxx 管理查看；GET /api/count
 *  4. 支持 CORS（GitHub Pages 前端跨域调用）
 *
 * 环境变量（Cloudflare Worker -> Settings -> Variables / Secrets）：
 *  AI_BASE_URL    中转站 Base URL，例如 https://xxx.com/v1
 *  AI_API_KEY     中转站 API Key（sk-开头）
 *  AI_MODEL       模型名，例如 grok-chat-fast
 *  AI_DAILY_LIMIT 每 IP 每日最大请求数，默认 15
 *  ADMIN_KEY      管理密钥（查看投稿用，GET /api/list?key=ADMIN_KEY）
 *
 * KV 绑定：
 *  ZSB_SUBMISSIONS —— 投稿存储
 */

export default {
  async fetch(request, env) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Access-Control-Max-Age": "86400",
    };

    const url = new URL(request.url);

    // 预检请求
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // ============ 投稿相关接口 ============
    if (url.pathname === "/api/submit" && request.method === "POST") {
      return handleSubmit(request, env, corsHeaders);
    }
    if (url.pathname === "/api/list" && request.method === "GET") {
      return handleList(request, env, corsHeaders);
    }
    if (url.pathname === "/api/get" && request.method === "GET") {
      return handleGet(request, env, corsHeaders);
    }
    if (url.pathname === "/api/delete" && request.method === "POST") {
      return handleDelete(request, env, corsHeaders);
    }
    if (url.pathname === "/api/count" && request.method === "GET") {
      return handleCount(env, corsHeaders);
    }

    // ============ 健康检查 ============
    if (request.method === "GET") {
      return new Response(
        JSON.stringify({ ok: true, name: "zsb-ai-proxy", services: ["ai", "submit"] }),
        { headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }

    // ============ AI 代理 ============
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }

    return handleAI(request, env, corsHeaders);
  },
};

// ---------- AI 代理 ----------
async function handleAI(request, env, corsHeaders) {
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

  const contentType = resp.headers.get("Content-Type") || "application/json";
  const text = await resp.text();

  return new Response(text, {
    status: resp.ok ? 200 : resp.status,
    headers: { "Content-Type": contentType, ...corsHeaders },
  });
}

// ---------- 投稿存储（支持手动填写 + 图片上传两种模式） ----------
async function handleSubmit(request, env, corsHeaders) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: "请求体不是有效JSON" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const subject = String(body.subject || "").trim();
  const subjects = ["高数", "计算机", "英语"];
  if (!subjects.includes(subject)) {
    return new Response(JSON.stringify({ error: "科目不合法，请选择 高数/计算机/英语" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const key = "sub_" + Date.now() + "_" + Math.random().toString(36).slice(2, 8);
  const baseRecord = {
    key: key,
    subject: subject,
    ip: ip,
    time: new Date().toISOString(),
  };

  // ===== 图片上传模式 =====
  if (body.type === "image") {
    const images = Array.isArray(body.images) ? body.images : [];
    if (images.length === 0) {
      return new Response(JSON.stringify({ error: "请至少上传一张图片" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }
    // 校验每张图片
    const cleanImages = [];
    let totalSize = 0;
    for (const img of images) {
      const filename = String(img.filename || "image.jpg").slice(0, 100);
      const base64 = String(img.base64 || "").trim();
      if (!base64 || base64.length < 100) {
        return new Response(JSON.stringify({ error: "图片 " + filename + " 数据无效" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
      // 去掉 data:image/xxx;base64, 前缀
      const pureBase64 = base64.replace(/^data:image\/[a-zA-Z+]+;base64,/, "");
      totalSize += pureBase64.length;
      cleanImages.push({ filename: filename, base64: pureBase64 });
    }
    // KV 单条最大 25MB，base64 后约 18.75MB 原始数据
    if (totalSize > 18000000) {
      return new Response(JSON.stringify({ error: "图片总大小超过限制（约18MB），请压缩后再上传" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }
    const record = {
      ...baseRecord,
      type: "image",
      note: String(body.note || "").trim().slice(0, 500),
      images: cleanImages,
    };
    try {
      await env.ZSB_SUBMISSIONS.put(key, JSON.stringify(record));
    } catch (e) {
      return new Response(JSON.stringify({ error: "存储失败：" + e.message }), {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }
    return new Response(
      JSON.stringify({ success: true, message: "图片上传成功！我们会尽快识别题目并审核入库。", key: key }),
      { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
    );
  }

  // ===== 手动填写模式（原有逻辑） =====
  const qtype = String(body.qtype || "单选").trim();
  const question = String(body.question || "").trim();
  const options = String(body.options || "").trim();
  const answer = String(body.answer || "").trim();
  const source = String(body.source || "").trim();
  const note = String(body.note || "").trim();

  if (question.length < 3) {
    return new Response(JSON.stringify({ error: "题目内容太短（至少3个字）" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  if (question.length > 3000 || options.length > 3000 || answer.length > 2000) {
    return new Response(JSON.stringify({ error: "内容超长，题目≤3000字、选项≤3000字、答案≤2000字" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const record = {
    ...baseRecord,
    type: "manual",
    qtype: qtype,
    question: question,
    options: options,
    answer: answer,
    source: source,
    note: note,
  };

  try {
    await env.ZSB_SUBMISSIONS.put(key, JSON.stringify(record));
  } catch (e) {
    return new Response(JSON.stringify({ error: "存储失败：" + e.message }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  return new Response(
    JSON.stringify({ success: true, message: "投稿成功！我们会尽快审核入库。", key: key }),
    { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
  );
}

// ---------- 管理查看投稿 ----------
async function handleList(request, env, corsHeaders) {
  const adminKey = env.ADMIN_KEY || "";
  const keyParam = request.url.includes("?")
    ? new URL(request.url).searchParams.get("key") || ""
    : "";
  if (!adminKey || keyParam !== adminKey) {
    return new Response(JSON.stringify({ error: "管理密钥不正确" }), {
      status: 403,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const out = [];
  let cursor = undefined;
  try {
    do {
      const page = await env.ZSB_SUBMISSIONS.list({ prefix: "sub_", limit: 1000, cursor });
      for (const item of page.keys) {
        const raw = await env.ZSB_SUBMISSIONS.get(item.name);
        if (raw) {
          try { out.push(JSON.parse(raw)); } catch (e) { /* 跳过坏数据 */ }
        }
      }
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);
  } catch (e) {
    return new Response(JSON.stringify({ error: "读取失败：" + e.message }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  out.sort((a, b) => (a.time < b.time ? 1 : -1));
  // 返回元数据，不含图片 base64（避免响应过大）
  const meta = out.map(function (r) {
    if (r.type === "image") {
      return {
        key: r.key, type: "image", subject: r.subject, time: r.time,
        note: r.note || "", imageCount: (r.images || []).length,
        filenames: (r.images || []).map(function (img) { return img.filename; }),
      };
    }
    return {
      key: r.key, type: r.type || "manual", subject: r.subject, time: r.time,
      qtype: r.qtype || "", question: (r.question || "").slice(0, 100),
      answer: r.answer || "", source: r.source || "", note: r.note || "",
    };
  });
  return new Response(
    JSON.stringify({ success: true, total: meta.length, items: meta }),
    { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
  );
}

// ---------- 获取单条投稿完整内容（含图片，管理员） ----------
async function handleGet(request, env, corsHeaders) {
  const adminKey = env.ADMIN_KEY || "";
  const url = new URL(request.url);
  const keyParam = url.searchParams.get("key") || "";
  const id = url.searchParams.get("id") || "";
  if (!adminKey || keyParam !== adminKey) {
    return new Response(JSON.stringify({ error: "管理密钥不正确" }), {
      status: 403,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  if (!id.startsWith("sub_")) {
    return new Response(JSON.stringify({ error: "id 不合法" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  let raw;
  try {
    raw = await env.ZSB_SUBMISSIONS.get(id);
  } catch (e) {
    return new Response(JSON.stringify({ error: "读取失败：" + e.message }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  if (!raw) {
    return new Response(JSON.stringify({ error: "投稿不存在" }), {
      status: 404,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  return new Response(raw, {
    status: 200,
    headers: { "Content-Type": "application/json", ...corsHeaders },
  });
}

// ---------- 删除投稿（管理员） ----------
async function handleDelete(request, env, corsHeaders) {
  const adminKey = env.ADMIN_KEY || "";
  const url = new URL(request.url);
  const keyParam = url.searchParams.get("key") || "";
  if (!adminKey || keyParam !== adminKey) {
    return new Response(JSON.stringify({ error: "管理密钥不正确" }), {
      status: 403,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: "请求体不是有效JSON" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  const id = String(body.id || "").trim();
  if (!id.startsWith("sub_")) {
    return new Response(JSON.stringify({ error: "id 不合法" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  try {
    await env.ZSB_SUBMISSIONS.delete(id);
  } catch (e) {
    return new Response(JSON.stringify({ error: "删除失败：" + e.message }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  return new Response(
    JSON.stringify({ success: true, message: "已删除 " + id }),
    { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
  );
}

// ---------- 投稿计数 ----------
async function handleCount(env, corsHeaders) {
  let total = 0;
  try {
    let cursor = undefined;
    do {
      const page = await env.ZSB_SUBMISSIONS.list({ prefix: "sub_", limit: 1000, cursor });
      total += page.keys.length;
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);
  } catch (e) {
    return new Response(JSON.stringify({ error: "读取失败：" + e.message }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }
  return new Response(
    JSON.stringify({ success: true, total: total }),
    { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders } }
  );
}
