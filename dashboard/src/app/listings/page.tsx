"use client"

import { useEffect, useState, useCallback } from "react"
import ListingsTable from "@/components/listings-table"
import FilterSidebar from "@/components/filter-sidebar"
import type { FilterValues } from "@/components/filter-sidebar"
import type { Listing, ApiResponse } from "@/lib/types"

function buildQueryString(filters: FilterValues): string {
  const params = new URLSearchParams()
  params.set("limit", "200")

  if (filters.maxPrice) params.set("max_price", filters.maxPrice)
  if (filters.minAcreage) params.set("min_acreage", filters.minAcreage)
  if (filters.state) params.set("state", filters.state)
  if (filters.county) params.set("county", filters.county)
  if (filters.sources.length === 1) params.set("source", filters.sources[0])

  return params.toString()
}

function applyClientFilters(listings: Listing[], filters: FilterValues): Listing[] {
  let result = listings

  if (filters.minPrice) {
    const min = parseInt(filters.minPrice, 10)
    result = result.filter(l => l.price >= min)
  }
  if (filters.maxAcreage) {
    const max = parseFloat(filters.maxAcreage)
    result = result.filter(l => l.acreage <= max)
  }
  if (filters.sources.length > 1) {
    result = result.filter(l => filters.sources.includes(l.source))
  }
  if (filters.features.includes("water")) {
    result = result.filter(l => l.has_water === 1)
  }
  if (filters.features.includes("utilities")) {
    result = result.filter(l => l.has_utilities === 1)
  }
  if (filters.features.includes("road_access")) {
    result = result.filter(l => l.has_road_access === 1)
  }

  return result
}

export default function ListingsPage() {
  const [allListings, setAllListings] = useState<Listing[]>([])
  const [filtered, setFiltered] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [currentFilters, setCurrentFilters] = useState<FilterValues | null>(null)

  const fetchListings = useCallback(async (filters?: FilterValues) => {
    setLoading(true)
    try {
      const qs = filters ? buildQueryString(filters) : "limit=200"
      const res = await fetch(`/api/listings?${qs}`)
      const data: ApiResponse<Listing[]> = await res.json()
      const listings = data.data ?? []
      setAllListings(listings)
      setFiltered(filters ? applyClientFilters(listings, filters) : listings)
    } catch {
      setAllListings([])
      setFiltered([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchListings()
  }, [fetchListings])

  function handleApplyFilters(filters: FilterValues) {
    setCurrentFilters(filters)
    fetchListings(filters)
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-zinc-900 dark:text-zinc-100">
        All Listings
      </h1>

      <div className="flex flex-col gap-4 lg:flex-row">
        <FilterSidebar onApply={handleApplyFilters} />

        <div className="min-w-0 flex-1">
          <p className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">
            {loading ? "Loading..." : `${filtered.length} listings`}
            {currentFilters && !loading ? " (filtered)" : ""}
          </p>

          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <p className="text-zinc-500 dark:text-zinc-400">Loading listings...</p>
            </div>
          ) : (
            <ListingsTable listings={filtered} />
          )}
        </div>
      </div>
    </div>
  )
}
