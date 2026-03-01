"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import { formatPrice, formatPPA, timeAgo } from "@/lib/format"
import type { Listing, ListingScores, ApiResponse } from "@/lib/types"

const ListingMap = dynamic(() => import("@/components/listing-map"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-zinc-500">Loading map...</p>
    </div>
  ),
})

function parseImageUrls(raw: string): string[] {
  try {
    const parsed = JSON.parse(raw || "[]")
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function FeatureBadge({ active, label }: { readonly active: boolean; readonly label: string }) {
  return (
    <span
      className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
        active
          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
      }`}
    >
      {label}: {active ? "Yes" : "Unknown"}
    </span>
  )
}

function scoreColor(score: number): string {
  if (score >= 80) return "text-green-600 dark:text-green-400"
  if (score >= 60) return "text-yellow-600 dark:text-yellow-400"
  if (score >= 40) return "text-zinc-600 dark:text-zinc-400"
  return "text-red-600 dark:text-red-400"
}

function Indicator({ good }: { readonly good: boolean | null }) {
  if (good === null) return <span className="text-zinc-400">{"\u2014"}</span>
  return good
    ? <span className="text-green-600">{"\u2705"}</span>
    : <span className="text-red-500">{"\u274C"}</span>
}

function ScoreRow({ label, value, indicator }: {
  readonly label: string
  readonly value: string
  readonly indicator: boolean | null
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-zinc-500 dark:text-zinc-400">{label}</span>
      <span className="flex items-center gap-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">
        {value} <Indicator good={indicator} />
      </span>
    </div>
  )
}

function LocationScorePanel({ scores }: { readonly scores: ListingScores }) {
  const matchScore = scores.match_score

  return (
    <div className="mt-6 rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="mb-4 text-lg font-bold text-zinc-900 dark:text-zinc-100">
        Location Score
      </h2>

      {matchScore != null && (
        <div className="mb-4">
          <span className={`text-3xl font-bold ${scoreColor(matchScore)}`}>
            {matchScore}
          </span>
          <span className="text-lg text-zinc-400">/100</span>
          <span className="ml-2">
            {matchScore >= 80 ? "\uD83D\uDFE2" : matchScore >= 60 ? "\uD83D\uDFE1" : "\uD83D\uDD34"}
          </span>
        </div>
      )}

      <div className="mb-4">
        <h3 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          {"\uD83D\uDCCD"} Proximity
        </h3>
        <div className="space-y-0.5">
          <ScoreRow
            label="Hospital"
            value={scores.nearest_hospital_miles != null
              ? `${scores.nearest_hospital_miles} mi${scores.nearest_hospital_name ? ` (${scores.nearest_hospital_name})` : ""}`
              : "Unknown"}
            indicator={scores.nearest_hospital_miles != null ? scores.nearest_hospital_miles < 25 : null}
          />
          <ScoreRow
            label="Walmart/Costco"
            value={scores.nearest_bigbox_miles != null
              ? `${scores.nearest_bigbox_miles} mi${scores.nearest_bigbox_name ? ` (${scores.nearest_bigbox_name})` : ""}`
              : "Unknown"}
            indicator={scores.nearest_bigbox_miles != null ? scores.nearest_bigbox_miles < 35 : null}
          />
          <ScoreRow
            label="Water"
            value={scores.nearest_water_miles != null
              ? `${scores.nearest_water_miles} mi${scores.nearest_water_type ? ` (${scores.nearest_water_type})` : ""}`
              : "Unknown"}
            indicator={scores.nearest_water_miles != null ? scores.nearest_water_miles < 5 : null}
          />
          <ScoreRow
            label="Hiking Trails"
            value={scores.nearest_trail_miles != null
              ? `${scores.nearest_trail_miles} mi${scores.nearest_trail_name ? ` (${scores.nearest_trail_name})` : ""}`
              : "Unknown"}
            indicator={scores.nearest_trail_miles != null ? scores.nearest_trail_miles < 15 : null}
          />
          <ScoreRow
            label="Offroad"
            value={scores.nearest_offroad_miles != null ? `${scores.nearest_offroad_miles} mi` : "Unknown"}
            indicator={scores.nearest_offroad_miles != null ? scores.nearest_offroad_miles < 30 : null}
          />
          <ScoreRow
            label="Ski Resort"
            value={scores.nearest_ski_resort_miles != null
              ? `${scores.nearest_ski_resort_miles} mi${scores.nearest_ski_resort_name ? ` (${scores.nearest_ski_resort_name})` : ""}`
              : "Unknown"}
            indicator={scores.nearest_ski_resort_miles != null ? scores.nearest_ski_resort_miles < 150 : null}
          />
          <ScoreRow
            label="School"
            value={scores.nearest_school_miles != null
              ? `${scores.nearest_school_miles} mi${scores.nearest_school_name ? ` (${scores.nearest_school_name})` : ""}`
              : "Unknown"}
            indicator={scores.nearest_school_miles != null ? scores.nearest_school_miles < 20 : null}
          />
        </div>
      </div>

      <div className="mb-4">
        <h3 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          {"\uD83C\uDFDB\uFE0F"} Area Info
        </h3>
        <div className="space-y-0.5">
          <ScoreRow
            label="Political"
            value={scores.county_political_lean ?? "Unknown"}
            indicator={scores.county_political_lean ? scores.county_political_lean.startsWith("R") : null}
          />
          <ScoreRow
            label="Property Tax"
            value={scores.county_property_tax_rate != null ? `${scores.county_property_tax_rate}%` : "Unknown"}
            indicator={scores.county_property_tax_rate != null ? scores.county_property_tax_rate < 1.2 : null}
          />
          <ScoreRow
            label="Military Discount"
            value={scores.county_mil_discount != null ? (scores.county_mil_discount ? "Yes" : "No") : "Unknown"}
            indicator={scores.county_mil_discount != null ? Boolean(scores.county_mil_discount) : null}
          />
          <ScoreRow
            label="Schools"
            value={scores.school_district_rating ?? "Unknown"}
            indicator={scores.school_district_rating
              ? ["Good", "Above Average"].includes(scores.school_district_rating)
              : null}
          />
          <ScoreRow
            label="Population"
            value={scores.county_population != null ? scores.county_population.toLocaleString() : "Unknown"}
            indicator={scores.county_population != null ? scores.county_population > 40000 : null}
          />
          <ScoreRow
            label="Growth (5yr)"
            value={scores.county_pop_growth_pct != null ? `${scores.county_pop_growth_pct > 0 ? "+" : ""}${scores.county_pop_growth_pct}%` : "Unknown"}
            indicator={scores.county_pop_growth_pct != null ? scores.county_pop_growth_pct > 5 : null}
          />
          <ScoreRow
            label="Median Age"
            value={scores.county_median_age != null ? `${scores.county_median_age}` : "Unknown"}
            indicator={scores.county_median_age != null ? scores.county_median_age < 40 : null}
          />
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          {"\uD83C\uDF24\uFE0F"} Climate
        </h3>
        <div className="space-y-0.5">
          <ScoreRow
            label="Snowfall"
            value={scores.avg_annual_snowfall_inches != null ? `${scores.avg_annual_snowfall_inches} in/yr` : "Unknown"}
            indicator={scores.avg_annual_snowfall_inches != null ? scores.avg_annual_snowfall_inches >= 20 : null}
          />
          <ScoreRow
            label="Sunny Days"
            value={scores.avg_sunny_days != null ? `${scores.avg_sunny_days}/yr` : "Unknown"}
            indicator={scores.avg_sunny_days != null ? scores.avg_sunny_days >= 170 : null}
          />
        </div>
      </div>
    </div>
  )
}

export default function ListingDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const [listing, setListing] = useState<Listing | null>(null)
  const [scores, setScores] = useState<ListingScores | null>(null)
  const [isFavorited, setIsFavorited] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [listingRes, favoritesRes, scoresRes] = await Promise.all([
          fetch(`/api/listings/${id}`),
          fetch("/api/favorites"),
          fetch(`/api/listings/${id}/scores`),
        ])
        const listingData: ApiResponse<Listing> = await listingRes.json()
        const favoritesData: ApiResponse<string[]> = await favoritesRes.json()
        const scoresData: ApiResponse<ListingScores | null> = await scoresRes.json()

        if (!listingData.success || !listingData.data) {
          setError(listingData.error ?? "Listing not found")
          return
        }

        setListing(listingData.data)
        setScores(scoresData.data ?? null)
        const favIds = favoritesData.data ?? []
        setIsFavorited(favIds.includes(id))
      } catch {
        setError("Failed to load listing")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const toggleFavorite = useCallback(async () => {
    const res = await fetch(`/api/favorites/${id}`, { method: "PATCH" })
    const data: ApiResponse<{ is_favorited: boolean }> = await res.json()
    if (data.success && data.data) {
      setIsFavorited(data.data.is_favorited)
    }
  }, [id])

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-zinc-500 dark:text-zinc-400">Loading listing...</p>
      </div>
    )
  }

  if (error || !listing) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <p className="text-zinc-500 dark:text-zinc-400">{error ?? "Listing not found"}</p>
        <button
          onClick={() => router.push("/listings")}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Back to listings
        </button>
      </div>
    )
  }

  const images = parseImageUrls(listing.image_urls)
  const address = [listing.address, listing.city, listing.county, listing.state, listing.zip_code]
    .filter(Boolean)
    .join(", ")

  return (
    <div>
      <button
        onClick={() => router.back()}
        className="mb-4 text-sm text-blue-600 hover:underline dark:text-blue-400"
      >
        &larr; Back
      </button>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <div className="mb-4 flex items-start justify-between gap-3">
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
              {listing.title}
            </h1>
            <button
              onClick={toggleFavorite}
              className="shrink-0 text-2xl transition-colors"
              aria-label={isFavorited ? "Remove from favorites" : "Add to favorites"}
            >
              {isFavorited ? (
                <span className="text-red-500">&#9829;</span>
              ) : (
                <span className="text-zinc-300 hover:text-red-400 dark:text-zinc-600">&#9825;</span>
              )}
            </button>
          </div>

          <div className="mb-6 flex flex-wrap gap-4">
            <div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Price</p>
              <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                {formatPrice(listing.price)}
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Acreage</p>
              <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                {listing.acreage.toFixed(1)} ac
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Price/Acre</p>
              <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                {formatPPA(listing.price_per_acre)}
              </p>
            </div>
          </div>

          {address && (
            <div className="mb-4">
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Location</p>
              <p className="text-sm text-zinc-900 dark:text-zinc-100">{address}</p>
            </div>
          )}

          <div className="mb-4 flex flex-wrap gap-2">
            <FeatureBadge active={listing.has_water === 1} label="Water" />
            <FeatureBadge active={listing.has_utilities === 1} label="Utilities" />
            <FeatureBadge active={listing.has_road_access === 1} label="Road Access" />
            {listing.zoning && (
              <span className="inline-block rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                Zoning: {listing.zoning}
              </span>
            )}
          </div>

          {listing.description && (
            <div className="mb-4">
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Description</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-300">
                {listing.description}
              </p>
            </div>
          )}

          {images.length > 0 && (
            <div className="mb-4">
              <p className="mb-2 text-xs text-zinc-500 dark:text-zinc-400">Images</p>
              <div className="grid grid-cols-2 gap-2">
                {images.map((url, idx) => (
                  <img
                    key={`${listing.id}-img-${idx}`}
                    src={url}
                    alt={`${listing.title} image ${idx + 1}`}
                    className="rounded-lg border border-zinc-200 object-cover dark:border-zinc-800"
                  />
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-3 text-sm">
            <span className="text-zinc-500 dark:text-zinc-400">
              Source: <span className="font-medium text-zinc-700 dark:text-zinc-300">{listing.source}</span>
            </span>
            <span className="text-zinc-500 dark:text-zinc-400">
              First seen: <span className="font-medium text-zinc-700 dark:text-zinc-300">{timeAgo(listing.first_seen_at)}</span>
            </span>
          </div>

          {listing.url && (
            <a
              href={listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              View original listing
            </a>
          )}
        </div>

        <div>
          <div className="h-[400px] overflow-hidden rounded-lg border border-zinc-200 lg:h-[500px] dark:border-zinc-800">
            <ListingMap listings={[listing]} />
          </div>

          {scores && <LocationScorePanel scores={scores} />}
        </div>
      </div>
    </div>
  )
}
