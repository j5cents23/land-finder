"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import { formatPrice, formatPPA, timeAgo } from "@/lib/format"
import type { Listing, ApiResponse } from "@/lib/types"

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

export default function ListingDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const [listing, setListing] = useState<Listing | null>(null)
  const [isFavorited, setIsFavorited] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [listingRes, favoritesRes] = await Promise.all([
          fetch(`/api/listings/${id}`),
          fetch("/api/favorites"),
        ])
        const listingData: ApiResponse<Listing> = await listingRes.json()
        const favoritesData: ApiResponse<string[]> = await favoritesRes.json()

        if (!listingData.success || !listingData.data) {
          setError(listingData.error ?? "Listing not found")
          return
        }

        setListing(listingData.data)
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

        <div className="h-[400px] overflow-hidden rounded-lg border border-zinc-200 lg:h-[500px] dark:border-zinc-800">
          <ListingMap listings={[listing]} />
        </div>
      </div>
    </div>
  )
}
