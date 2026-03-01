"use client"

import { useState } from "react"

const SOURCES = ["REALTOR", "CRAIGSLIST", "LANDWATCH", "LAND_COM", "ZILLOW", "FACEBOOK"] as const
const FEATURES = [
  { key: "water", label: "Water" },
  { key: "utilities", label: "Utilities" },
  { key: "road_access", label: "Road Access" },
] as const

export interface FilterValues {
  minPrice: string
  maxPrice: string
  minAcreage: string
  maxAcreage: string
  state: string
  county: string
  sources: string[]
  features: string[]
}

interface FilterSidebarProps {
  readonly onApply: (filters: FilterValues) => void
}

const EMPTY_FILTERS: FilterValues = {
  minPrice: "",
  maxPrice: "",
  minAcreage: "",
  maxAcreage: "",
  state: "",
  county: "",
  sources: [],
  features: [],
}

export default function FilterSidebar({ onApply }: FilterSidebarProps) {
  const [filters, setFilters] = useState<FilterValues>({ ...EMPTY_FILTERS })

  function handleTextChange(field: keyof FilterValues, value: string) {
    setFilters(prev => ({ ...prev, [field]: value }))
  }

  function handleSourceToggle(source: string) {
    setFilters(prev => {
      const sources = prev.sources.includes(source)
        ? prev.sources.filter(s => s !== source)
        : [...prev.sources, source]
      return { ...prev, sources }
    })
  }

  function handleFeatureToggle(feature: string) {
    setFilters(prev => {
      const features = prev.features.includes(feature)
        ? prev.features.filter(f => f !== feature)
        : [...prev.features, feature]
      return { ...prev, features }
    })
  }

  function handleApply() {
    onApply(filters)
  }

  function handleReset() {
    const reset = { ...EMPTY_FILTERS }
    setFilters(reset)
    onApply(reset)
  }

  return (
    <aside className="w-full space-y-5 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 lg:w-64">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Filters</h2>

      <div>
        <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Price Range ($)</label>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.minPrice}
            onChange={e => handleTextChange("minPrice", e.target.value)}
            className="w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.maxPrice}
            onChange={e => handleTextChange("maxPrice", e.target.value)}
            className="w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Acreage Range</label>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.minAcreage}
            onChange={e => handleTextChange("minAcreage", e.target.value)}
            className="w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.maxAcreage}
            onChange={e => handleTextChange("maxAcreage", e.target.value)}
            className="w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">State</label>
        <input
          type="text"
          placeholder="e.g. TX"
          value={filters.state}
          onChange={e => handleTextChange("state", e.target.value)}
          className="w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">County</label>
        <input
          type="text"
          placeholder="e.g. Travis"
          value={filters.county}
          onChange={e => handleTextChange("county", e.target.value)}
          className="w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Source</label>
        <div className="space-y-1">
          {SOURCES.map(source => (
            <label key={source} className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
              <input
                type="checkbox"
                checked={filters.sources.includes(source)}
                onChange={() => handleSourceToggle(source)}
                className="rounded border-zinc-300 dark:border-zinc-600"
              />
              {source.charAt(0) + source.slice(1).toLowerCase().replace("_", ".")}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Features</label>
        <div className="space-y-1">
          {FEATURES.map(feat => (
            <label key={feat.key} className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
              <input
                type="checkbox"
                checked={filters.features.includes(feat.key)}
                onChange={() => handleFeatureToggle(feat.key)}
                className="rounded border-zinc-300 dark:border-zinc-600"
              />
              {feat.label}
            </label>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleApply}
          className="flex-1 rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          Apply
        </button>
        <button
          onClick={handleReset}
          className="rounded border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          Reset
        </button>
      </div>
    </aside>
  )
}
