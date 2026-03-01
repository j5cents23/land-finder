import { NextRequest, NextResponse } from "next/server"
import { getDb } from "@/lib/db"
import type { ApiResponse, ListingScores } from "@/lib/types"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const db = getDb()
  try {
    const row = db.prepare("SELECT * FROM listing_scores WHERE listing_id = ?").get(id) as ListingScores | undefined
    return NextResponse.json({ success: true, data: row ?? null } satisfies ApiResponse<ListingScores | null>)
  } finally {
    db.close()
  }
}
