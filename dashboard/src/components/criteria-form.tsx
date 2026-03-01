"use client"

import { useState } from "react"
import type { ApiResponse, SearchCriteria } from "@/lib/types"

interface CriteriaFormProps {
  readonly onCreated: (criteria: SearchCriteria) => void
}

interface FormState {
  name: string
  min_acreage: string
  max_price: string
  max_ppa: string
  states: string
  counties: string
  center_lat: string
  center_lng: string
  radius_miles: string
  require_water: boolean
  require_utils: boolean
  require_road: boolean
}

const INITIAL_FORM: FormState = {
  name: "",
  min_acreage: "",
  max_price: "",
  max_ppa: "",
  states: "",
  counties: "",
  center_lat: "",
  center_lng: "",
  radius_miles: "",
  require_water: false,
  require_utils: false,
  require_road: false,
}

export default function CriteriaForm({ onCreated }: CriteriaFormProps) {
  const [form, setForm] = useState<FormState>({ ...INITIAL_FORM })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handleTextChange(field: keyof FormState, value: string) {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  function handleCheckboxChange(field: keyof FormState) {
    setForm(prev => ({ ...prev, [field]: !prev[field] }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!form.name.trim()) {
      setError("Name is required")
      return
    }

    setSubmitting(true)
    try {
      const body = {
        name: form.name.trim(),
        min_acreage: form.min_acreage ? parseFloat(form.min_acreage) : null,
        max_price: form.max_price ? parseInt(form.max_price, 10) : null,
        max_ppa: form.max_ppa ? parseInt(form.max_ppa, 10) : null,
        states: form.states ? form.states.split(",").map(s => s.trim()).filter(Boolean) : [],
        counties: form.counties ? form.counties.split(",").map(s => s.trim()).filter(Boolean) : [],
        center_lat: form.center_lat ? parseFloat(form.center_lat) : null,
        center_lng: form.center_lng ? parseFloat(form.center_lng) : null,
        radius_miles: form.radius_miles ? parseFloat(form.radius_miles) : null,
        require_water: form.require_water,
        require_utils: form.require_utils,
        require_road: form.require_road,
      }

      const res = await fetch("/api/criteria", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      const data: ApiResponse<SearchCriteria> = await res.json()

      if (!data.success || !data.data) {
        setError(data.error ?? "Failed to create criteria")
        return
      }

      onCreated(data.data)
      setForm({ ...INITIAL_FORM })
    } catch {
      setError("Failed to create criteria")
    } finally {
      setSubmitting(false)
    }
  }

  const inputClass = "w-full rounded border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
  const labelClass = "mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400"

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">New Search Criteria</h2>

      {error && (
        <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </p>
      )}

      <div>
        <label className={labelClass}>Name *</label>
        <input
          type="text"
          value={form.name}
          onChange={e => handleTextChange("name", e.target.value)}
          placeholder="e.g. Texas Rural Land"
          className={inputClass}
          required
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label className={labelClass}>Min Acreage</label>
          <input
            type="number"
            value={form.min_acreage}
            onChange={e => handleTextChange("min_acreage", e.target.value)}
            placeholder="e.g. 5"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Max Price (cents)</label>
          <input
            type="number"
            value={form.max_price}
            onChange={e => handleTextChange("max_price", e.target.value)}
            placeholder="e.g. 5000000"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Max Price/Acre (cents)</label>
          <input
            type="number"
            value={form.max_ppa}
            onChange={e => handleTextChange("max_ppa", e.target.value)}
            placeholder="e.g. 500000"
            className={inputClass}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>States (comma-separated)</label>
          <input
            type="text"
            value={form.states}
            onChange={e => handleTextChange("states", e.target.value)}
            placeholder="e.g. TX, OK, AR"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Counties (comma-separated)</label>
          <input
            type="text"
            value={form.counties}
            onChange={e => handleTextChange("counties", e.target.value)}
            placeholder="e.g. Travis, Williamson"
            className={inputClass}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label className={labelClass}>Center Latitude</label>
          <input
            type="number"
            step="any"
            value={form.center_lat}
            onChange={e => handleTextChange("center_lat", e.target.value)}
            placeholder="e.g. 30.267"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Center Longitude</label>
          <input
            type="number"
            step="any"
            value={form.center_lng}
            onChange={e => handleTextChange("center_lng", e.target.value)}
            placeholder="e.g. -97.743"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Radius (miles)</label>
          <input
            type="number"
            value={form.radius_miles}
            onChange={e => handleTextChange("radius_miles", e.target.value)}
            placeholder="e.g. 50"
            className={inputClass}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-4">
        <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={form.require_water}
            onChange={() => handleCheckboxChange("require_water")}
            className="rounded border-zinc-300 dark:border-zinc-600"
          />
          Require water
        </label>
        <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={form.require_utils}
            onChange={() => handleCheckboxChange("require_utils")}
            className="rounded border-zinc-300 dark:border-zinc-600"
          />
          Require utilities
        </label>
        <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            checked={form.require_road}
            onChange={() => handleCheckboxChange("require_road")}
            className="rounded border-zinc-300 dark:border-zinc-600"
          />
          Require road access
        </label>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Creating..." : "Create Criteria"}
      </button>
    </form>
  )
}
