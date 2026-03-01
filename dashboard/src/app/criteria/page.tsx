"use client"

import { useEffect, useState, useCallback } from "react"
import CriteriaForm from "@/components/criteria-form"
import type { SearchCriteria, ApiResponse } from "@/lib/types"

function parseJsonArray(raw: string): string[] {
  try {
    const parsed = JSON.parse(raw || "[]")
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export default function CriteriaPage() {
  const [criteria, setCriteria] = useState<SearchCriteria[]>([])
  const [loading, setLoading] = useState(true)

  const fetchCriteria = useCallback(async () => {
    try {
      const res = await fetch("/api/criteria")
      const data: ApiResponse<SearchCriteria[]> = await res.json()
      setCriteria(data.data ?? [])
    } catch {
      setCriteria([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCriteria()
  }, [fetchCriteria])

  function handleCreated(newCriteria: SearchCriteria) {
    setCriteria(prev => [...prev, newCriteria])
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-zinc-500 dark:text-zinc-400">Loading criteria...</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-zinc-900 dark:text-zinc-100">
        Search Criteria
      </h1>

      <div className="mb-8">
        <CriteriaForm onCreated={handleCreated} />
      </div>

      <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        Existing Criteria ({criteria.length})
      </h2>

      {criteria.length === 0 ? (
        <p className="text-zinc-500 dark:text-zinc-400">
          No search criteria configured. Create one above to get started.
        </p>
      ) : (
        <div className="space-y-3">
          {criteria.map(c => {
            const states = parseJsonArray(c.states)
            const counties = parseJsonArray(c.counties)

            return (
              <div
                key={c.id}
                className="flex items-start justify-between gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-zinc-900 dark:text-zinc-100">{c.name}</h3>
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.is_active === 1
                          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
                      }`}
                    >
                      {c.is_active === 1 ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                    {c.min_acreage && <span>Min {c.min_acreage} ac</span>}
                    {c.max_price && <span>Max ${(c.max_price / 100).toLocaleString()}</span>}
                    {c.max_ppa && <span>Max ${(c.max_ppa / 100).toLocaleString()}/ac</span>}
                    {states.length > 0 && <span>States: {states.join(", ")}</span>}
                    {counties.length > 0 && <span>Counties: {counties.join(", ")}</span>}
                    {c.radius_miles && <span>Within {c.radius_miles} mi</span>}
                    {c.require_water === 1 && <span>Water required</span>}
                    {c.require_utils === 1 && <span>Utilities required</span>}
                    {c.require_road === 1 && <span>Road access required</span>}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
