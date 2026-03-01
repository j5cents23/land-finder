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
  const sortBy = params.get("sort")

  const db = getDb()

  try {
    const conditions: string[] = []
    const values: unknown[] = []

    if (activeOnly) {
      conditions.push("l.is_active = 1")
    }
    if (state) {
      conditions.push("l.state = ?")
      values.push(state)
    }
    if (county) {
      conditions.push("l.county = ?")
      values.push(county)
    }
    if (minAcreage) {
      conditions.push("l.acreage >= ?")
      values.push(parseFloat(minAcreage))
    }
    if (maxPrice) {
      conditions.push("l.price <= ?")
      values.push(parseInt(maxPrice, 10))
    }
    if (source) {
      conditions.push("l.source = ?")
      values.push(source)
    }

    const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : ""

    const orderClause = sortBy === "score"
      ? "ORDER BY ls.match_score DESC"
      : "ORDER BY l.first_seen_at DESC"

    const countRow = db.prepare(
      `SELECT COUNT(*) as total FROM listings l ${where}`
    ).get(...values) as { total: number }

    const rows = db.prepare(
      `SELECT l.*, ls.match_score, ls.nearest_hospital_miles, ls.nearest_bigbox_miles,
              ls.nearest_water_miles, ls.nearest_trail_miles, ls.nearest_ski_resort_miles,
              ls.county_political_lean, ls.county_property_tax_rate, ls.school_district_rating,
              ls.avg_annual_snowfall_inches, ls.avg_sunny_days, ls.county_pop_growth_pct,
              ls.county_median_age, ls.county_population, ls.county_mil_discount
       FROM listings l
       LEFT JOIN listing_scores ls ON l.id = ls.listing_id
       ${where} ${orderClause} LIMIT ? OFFSET ?`
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
