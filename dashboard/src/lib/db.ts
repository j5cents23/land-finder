import Database from "better-sqlite3"
import path from "path"

const DB_PATH = path.join(process.cwd(), "..", "db", "land_finder.db")

export function getDb(): Database.Database {
  return new Database(DB_PATH, { readonly: true })
}

export function getWritableDb(): Database.Database {
  return new Database(DB_PATH)
}
