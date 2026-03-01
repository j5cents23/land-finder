import { NextRequest, NextResponse } from "next/server"
import { getDb } from "@/lib/db"
import type { ApiResponse, Listing } from "@/lib/types"

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams
  const page = parseInt(params.get("page") ?? "1", 10)
  const limit = parseInt(params.get("limit") ?? "50", 10)
  const offset = (page - 1) * limit

  const state = params.get("state")
  const county = params.get("county")
  const minAcreage = params.get("min_acreage")
  const maxPrice = params.get("max_price")
  const source = params.get("source")
  const activeOnly = params.get("active") !== "false"

  const db = getDb()

  try {
    const conditions: string[] = []
    const values: unknown[] = []

    if (activeOnly) {
      conditions.push("is_active = 1")
    }
    if (state) {
      conditions.push("state = ?")
      values.push(state)
    }
    if (county) {
      conditions.push("county = ?")
      values.push(county)
    }
    if (minAcreage) {
      conditions.push("acreage >= ?")
      values.push(parseFloat(minAcreage))
    }
    if (maxPrice) {
      conditions.push("price <= ?")
      values.push(parseInt(maxPrice, 10))
    }
    if (source) {
      conditions.push("source = ?")
      values.push(source)
    }

    const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : ""

    const countRow = db.prepare(
      `SELECT COUNT(*) as total FROM listings ${where}`
    ).get(...values) as { total: number }

    const rows = db.prepare(
      `SELECT * FROM listings ${where} ORDER BY first_seen_at DESC LIMIT ? OFFSET ?`
    ).all(...values, limit, offset)

    const response: ApiResponse<Listing[]> = {
      success: true,
      data: rows as Listing[],
      meta: { total: countRow.total, page, limit },
    }
    return NextResponse.json(response)
  } finally {
    db.close()
  }
}
