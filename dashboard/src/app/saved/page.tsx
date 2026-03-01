"use client"

import { useEffect, useState, useCallback } from "react"
import ListingCard from "@/components/listing-card"
import type { Listing, ApiResponse } from "@/lib/types"

export default function SavedPage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    try {
      const [listingsRes, favoritesRes] = await Promise.all([
        fetch("/api/listings?limit=500"),
        fetch("/api/favorites"),
      ])
      const listingsData: ApiResponse<Listing[]> = await listingsRes.json()
      const favoritesData: ApiResponse<string[]> = await favoritesRes.json()

      const favIds = new Set(favoritesData.data ?? [])
      setFavoriteIds(favIds)
      setListings((listingsData.data ?? []).filter(l => favIds.has(l.id)))
    } catch {
      setListings([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

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
      if (!data.data.is_favorited) {
        setListings(prev => prev.filter(l => l.id !== id))
      }
    }
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-zinc-500 dark:text-zinc-400">Loading saved listings...</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-zinc-900 dark:text-zinc-100">
        Saved Listings
      </h1>

      <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
        {listings.length} saved listing{listings.length !== 1 ? "s" : ""}
      </p>

      {listings.length === 0 ? (
        <p className="py-12 text-center text-zinc-500 dark:text-zinc-400">
          No saved listings yet. Favorite some listings to see them here.
        </p>
      ) : (
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
      )}
    </div>
  )
}
