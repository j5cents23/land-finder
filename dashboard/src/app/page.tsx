"use client"

import { useEffect, useState, useCallback } from "react"
import dynamic from "next/dynamic"
import ListingCard from "@/components/listing-card"
import type { Listing, ApiResponse } from "@/lib/types"

const ListingMap = dynamic(() => import("@/components/listing-map"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-zinc-500">Loading map...</p>
    </div>
  ),
})

export default function HomePage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [listingsRes, favoritesRes] = await Promise.all([
          fetch("/api/listings?limit=100"),
          fetch("/api/favorites"),
        ])
        const listingsData: ApiResponse<Listing[]> = await listingsRes.json()
        const favoritesData: ApiResponse<string[]> = await favoritesRes.json()

        setListings(listingsData.data ?? [])
        setFavoriteIds(new Set(favoritesData.data ?? []))
      } catch {
        setListings([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const toggleFavorite = useCallback(async (id: string) => {
    const res = await fetch(`/api/favorites/${id}`, { method: "PATCH" })
    const data: ApiResponse<{ is_favorited: boolean }> = await res.json()
    if (data.success && data.data) {
      setFavoriteIds(prev => {
        const next = new Set(prev)
        if (data.data?.is_favorited) {
          next.add(id)
        } else {
          next.delete(id)
        }
        return next
      })
    }
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-zinc-500 dark:text-zinc-400">Loading listings...</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-zinc-900 dark:text-zinc-100">
        Land Listings
      </h1>

      <div className="mb-6 h-[50vh] overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
        <ListingMap listings={listings} />
      </div>

      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {listings.length} listings
        </p>
        <div className="flex gap-2 text-xs text-zinc-500 dark:text-zinc-400">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500" /> New
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-blue-500" /> Older
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" /> Hot deal
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {listings.map(listing => (
          <ListingCard
            key={listing.id}
            listing={listing}
            isFavorited={favoriteIds.has(listing.id)}
            onToggleFavorite={toggleFavorite}
          />
        ))}
      </div>

      {listings.length === 0 && (
        <p className="py-12 text-center text-zinc-500 dark:text-zinc-400">
          No listings found. Run the scraper to populate data.
        </p>
      )}
    </div>
  )
}
