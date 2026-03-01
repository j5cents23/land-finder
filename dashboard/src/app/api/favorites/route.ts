import { NextResponse } from "next/server"
import { getWritableDb } from "@/lib/db"

export async function GET() {
  const db = getWritableDb()
  try {
    db.prepare("CREATE TABLE IF NOT EXISTS favorites (listing_id TEXT PRIMARY KEY)").run()
    const rows = db.prepare("SELECT listing_id FROM favorites").all() as { listing_id: string }[]
    return NextResponse.json({ success: true, data: rows.map(r => r.listing_id) })
  } finally {
    db.close()
  }
}
