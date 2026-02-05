// src/app/api/admin/import/route.js
import { getServerSession } from "next-auth/next";
import { authOptions } from "../../auth/[...nextauth]/route";

export async function POST(req) {
  const session = await getServerSession(authOptions);

  if (!session || !session.user || !session.user.email) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const body = await req.json();
  const event_id = body?.event_id;

  if (!event_id) {
    return new Response(JSON.stringify({ error: "Missing event_id" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const baseApiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!baseApiUrl) {
    return new Response(JSON.stringify({ error: "Missing NEXT_PUBLIC_API_URL" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  const adminToken = process.env.NEXT_PRIVATE_ADMIN_TOKEN;
  if (!adminToken) {
    return new Response(
      JSON.stringify({ error: "Missing NEXT_PRIVATE_ADMIN_TOKEN" }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  const djangoUrl = `${baseApiUrl}/admin/import/${encodeURIComponent(event_id)}/`;

  try {
    const res = await fetch(djangoUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Token": adminToken,
        "X-User-Email": session.user.email,
      },
      body: JSON.stringify({ notes: body?.notes || null }),
    });

    const text = await res.text();
    const contentType = res.headers.get("content-type") || "text/plain";

    return new Response(text, {
      status: res.status,
      headers: { "Content-Type": contentType },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: "Failed to reach backend", details: err?.message }),
      {
        status: 502,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}
