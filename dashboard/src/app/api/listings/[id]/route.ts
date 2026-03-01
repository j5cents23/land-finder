import { NextRequest, NextResponse } from "next/server"
import { getDb } from "@/lib/db"
import type { ApiResponse, Listing } from "@/lib/types"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const db = getDb()
  try {
    const row = db.prepare("SELECT * FROM listings WHERE id = ?").get(id) as Listing | undefined
    if (!row) {
      return NextResponse.json(
        { success: false, error: "Listing not found" } satisfies ApiResponse<never>,
        { status: 404 }
      )
    }
    return NextResponse.json({ success: true, data: row } satisfies ApiResponse<Listing>)
  } finally {
    db.close()
  }
}
