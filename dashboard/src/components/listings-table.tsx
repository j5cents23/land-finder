"use client"

import { useState, useMemo } from "react"
import Link from "next/link"
import { formatPrice, formatPPA, timeAgo } from "@/lib/format"
import type { Listing } from "@/lib/types"

interface ListingsTableProps {
  readonly listings: Listing[]
}

type SortKey = "title" | "price" | "acreage" | "price_per_acre" | "county" | "state" | "source" | "first_seen_at"
type SortDir = "asc" | "desc"

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "title", label: "Title" },
  { key: "price", label: "Price" },
  { key: "acreage", label: "Acreage" },
  { key: "price_per_acre", label: "Price/Acre" },
  { key: "county", label: "County" },
  { key: "state", label: "State" },
  { key: "source", label: "Source" },
  { key: "first_seen_at", label: "First Seen" },
]

function compareFn(a: Listing, b: Listing, key: SortKey): number {
  const valA = a[key]
  const valB = b[key]
  if (typeof valA === "number" && typeof valB === "number") return valA - valB
  return String(valA ?? "").localeCompare(String(valB ?? ""))
}

export default function ListingsTable({ listings }: ListingsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("first_seen_at")
  const [sortDir, setSortDir] = useState<SortDir>("desc")

  const sorted = useMemo(() => {
    const copy = [...listings]
    copy.sort((a, b) => {
      const result = compareFn(a, b, sortKey)
      return sortDir === "asc" ? result : -result
    })
    return copy
  }, [listings, sortKey, sortDir])

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir(prev => (prev === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
          <tr>
            {COLUMNS.map(col => (
              <th
                key={col.key}
                className="cursor-pointer whitespace-nowrap px-4 py-3 font-medium text-zinc-600 transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key && (
                  <span className="ml-1">{sortDir === "asc" ? "\u2191" : "\u2193"}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {sorted.map(listing => (
            <tr
              key={listing.id}
              className="transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-900/50"
            >
              <td className="max-w-xs truncate px-4 py-3">
                <Link
                  href={`/listings/${listing.id}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {listing.title}
                </Link>
              </td>
              <td className="whitespace-nowrap px-4 py-3 font-medium">
                {formatPrice(listing.price)}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                {listing.acreage.toFixed(1)} ac
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                {formatPPA(listing.price_per_acre)}
              </td>
              <td className="whitespace-nowrap px-4 py-3">{listing.county}</td>
              <td className="whitespace-nowrap px-4 py-3">{listing.state}</td>
              <td className="whitespace-nowrap px-4 py-3">{listing.source}</td>
              <td className="whitespace-nowrap px-4 py-3 text-zinc-500 dark:text-zinc-400">
                {timeAgo(listing.first_seen_at)}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={COLUMNS.length} className="px-4 py-12 text-center text-zinc-500">
                No listings match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
