import { NextRequest, NextResponse } from "next/server"
import { getDb, getWritableDb } from "@/lib/db"
import type { ApiResponse, SearchCriteria } from "@/lib/types"
import { randomUUID } from "crypto"

export async function GET() {
  const db = getDb()
  try {
    const rows = db.prepare("SELECT * FROM search_criteria ORDER BY name").all() as SearchCriteria[]
    return NextResponse.json({ success: true, data: rows } satisfies ApiResponse<SearchCriteria[]>)
  } finally {
    db.close()
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const db = getWritableDb()
  try {
    const id = randomUUID()
    db.prepare(`
      INSERT INTO search_criteria (id, name, min_acreage, max_price, max_ppa, states, counties,
        center_lat, center_lng, radius_miles, require_water, require_utils, require_road,
        zoning_types, is_active)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      id, body.name, body.min_acreage ?? null, body.max_price ?? null,
      body.max_ppa ?? null, JSON.stringify(body.states ?? []),
      JSON.stringify(body.counties ?? []), body.center_lat ?? null,
      body.center_lng ?? null, body.radius_miles ?? null,
      body.require_water ? 1 : 0, body.require_utils ? 1 : 0,
      body.require_road ? 1 : 0, JSON.stringify(body.zoning_types ?? []),
      body.is_active !== false ? 1 : 0
    )
    const created = db.prepare("SELECT * FROM search_criteria WHERE id = ?").get(id) as SearchCriteria
    return NextResponse.json(
      { success: true, data: created } satisfies ApiResponse<SearchCriteria>,
      { status: 201 }
    )
  } finally {
    db.close()
  }
}
