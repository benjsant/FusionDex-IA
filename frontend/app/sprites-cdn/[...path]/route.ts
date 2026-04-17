import { NextRequest, NextResponse } from "next/server";

// Proxy pour les sprites servis par le sidecar nginx. Même logique que
// /api/* mais cible la racine nginx (dossier /sprites/...). Binaires PNG.
const SPRITES_URL =
  process.env.SPRITES_INTERNAL_URL || "http://localhost:58080";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const target = `${SPRITES_URL}/sprites/${path.join("/")}${req.nextUrl.search}`;
  try {
    const upstream = await fetch(target, { cache: "no-store" });
    const resHeaders = new Headers(upstream.headers);
    ["transfer-encoding", "connection"].forEach((h) => resHeaders.delete(h));
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: resHeaders,
    });
  } catch (err) {
    return NextResponse.json(
      { detail: `Sprites proxy error: ${(err as Error).message}` },
      { status: 502 },
    );
  }
}
