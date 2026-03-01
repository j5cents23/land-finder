import { NextRequest, NextResponse } from "next/server"
import { getWritableDb } from "@/lib/db"
import type { ApiResponse } from "@/lib/types"

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const db = getWritableDb()
  try {
    db.prepare(`
      CREATE TABLE IF NOT EXISTS favorites (
        listing_id TEXT PRIMARY KEY
      )
    `).run()

    const existing = db.prepare("SELECT listing_id FROM favorites WHERE listing_id = ?").get(id)
    if (existing) {
      db.prepare("DELETE FROM favorites WHERE listing_id = ?").run(id)
      return NextResponse.json({ success: true, data: { is_favorited: false } } satisfies ApiResponse<{ is_favorited: boolean }>)
    } else {
      db.prepare("INSERT INTO favorites (listing_id) VALUES (?)").run(id)
      return NextResponse.json({ success: true, data: { is_favorited: true } } satisfies ApiResponse<{ is_favorited: boolean }>)
    }
  } finally {
    db.close()
  }
}
