"use client"

import Link from "next/link"
import { formatPrice, formatPPA, timeAgo } from "@/lib/format"
import type { Listing } from "@/lib/types"

interface ListingCardProps {
  readonly listing: Listing
  readonly isFavorited: boolean
  readonly onToggleFavorite: (id: string) => void
}

const SOURCE_COLORS: Record<string, string> = {
  craigslist: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  landwatch: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  land_com: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  zillow: "bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200",
  facebook: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200",
}

function ScoreBadge({ score }: { readonly score: number | null }) {
  if (score == null || score < 40) return null

  const colorClass = score >= 80
    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
    : score >= 60
      ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
      : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"

  const label = score >= 80 ? `\uD83C\uDFAF ${score}` : `${score}`

  return (
    <span className={`absolute right-2 top-2 inline-block rounded-full px-2 py-0.5 text-xs font-bold ${colorClass}`}>
      {label}
    </span>
  )
}

export default function ListingCard({ listing, isFavorited, onToggleFavorite }: ListingCardProps) {
  const sourceClass = SOURCE_COLORS[listing.source] ?? "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200"

  return (
    <div className="group relative rounded-lg border border-zinc-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900">
      <ScoreBadge score={listing.match_score} />

      <div className="mb-2 flex items-start justify-between gap-2">
        <Link
          href={`/listings/${listing.id}`}
          className="text-sm font-semibold leading-tight text-zinc-900 hover:text-blue-600 dark:text-zinc-100 dark:hover:text-blue-400"
        >
          {listing.title}
        </Link>
        <button
          onClick={() => onToggleFavorite(listing.id)}
          className="shrink-0 text-lg transition-colors"
          aria-label={isFavorited ? "Remove from favorites" : "Add to favorites"}
        >
          {isFavorited ? (
            <span className="text-red-500">&#9829;</span>
          ) : (
            <span className="text-zinc-300 hover:text-red-400 dark:text-zinc-600">&#9825;</span>
          )}
        </button>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <span className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
          {formatPrice(listing.price)}
        </span>
        <span className="flex items-center text-sm text-zinc-500 dark:text-zinc-400">
          {listing.acreage.toFixed(1)} ac
        </span>
        <span className="flex items-center text-sm text-zinc-500 dark:text-zinc-400">
          {formatPPA(listing.price_per_acre)}
        </span>
      </div>

      <div className="mb-2 text-xs text-zinc-500 dark:text-zinc-400">
        {[listing.county, listing.state].filter(Boolean).join(", ")}
      </div>

      <div className="flex items-center justify-between">
        <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${sourceClass}`}>
          {listing.source}
        </span>
        <span className="text-xs text-zinc-400 dark:text-zinc-500">
          {timeAgo(listing.first_seen_at)}
        </span>
      </div>
    </div>
  )
}
