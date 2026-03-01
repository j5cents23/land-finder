import { NextResponse } from "next/server"
import { readFileSync, existsSync } from "fs"
import path from "path"
import type { ApiResponse } from "@/lib/types"

export async function GET() {
  const runsPath = path.join(process.cwd(), "..", "runs.json")
  if (!existsSync(runsPath)) {
    return NextResponse.json({ success: true, data: [] } satisfies ApiResponse<unknown[]>)
  }
  const runs = JSON.parse(readFileSync(runsPath, "utf-8"))
  return NextResponse.json({ success: true, data: runs } satisfies ApiResponse<unknown[]>)
}
