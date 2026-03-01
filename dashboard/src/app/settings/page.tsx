"use client"

import { useEffect, useState, useCallback } from "react"
import { timeAgo } from "@/lib/format"
import type { ApiResponse } from "@/lib/types"

interface SpiderStatus {
  name: string
  items_scraped: number
  error?: string
}

interface ScraperRun {
  id: string
  started_at: string
  finished_at: string
  total_raw: number
  new_matches: number
  spiders: SpiderStatus[]
}

export default function SettingsPage() {
  const [runs, setRuns] = useState<ScraperRun[]>([])
  const [loading, setLoading] = useState(true)

  const fetchRuns = useCallback(async () => {
    try {
      const res = await fetch("/api/runs")
      const data: ApiResponse<ScraperRun[]> = await res.json()
      setRuns(data.data ?? [])
    } catch {
      setRuns([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRuns()
  }, [fetchRuns])

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-zinc-500 dark:text-zinc-400">Loading settings...</p>
      </div>
    )
  }

  const latestRun = runs.length > 0 ? runs[0] : null
  const recentRuns = runs.slice(0, 5)

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-zinc-900 dark:text-zinc-100">
        Settings
      </h1>

      <div className="mb-8">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Last Scraper Run
        </h2>

        {latestRun ? (
          <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Timestamp</p>
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  {timeAgo(latestRun.started_at)}
                </p>
                <p className="text-xs text-zinc-400 dark:text-zinc-500">
                  {new Date(latestRun.started_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Total Raw Results</p>
                <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                  {latestRun.total_raw}
                </p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">New Matches</p>
                <p className="text-xl font-bold text-green-600 dark:text-green-400">
                  {latestRun.new_matches}
                </p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Spiders</p>
                <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                  {latestRun.spiders?.length ?? 0}
                </p>
              </div>
            </div>

            {latestRun.spiders && latestRun.spiders.length > 0 && (
              <div className="mt-4 border-t border-zinc-100 pt-4 dark:border-zinc-800">
                <p className="mb-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                  Spider Statuses
                </p>
                <div className="flex flex-wrap gap-2">
                  {latestRun.spiders.map(spider => (
                    <span
                      key={spider.name}
                      className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${
                        spider.error
                          ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                          : "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      }`}
                    >
                      {spider.name}: {spider.items_scraped} items
                      {spider.error && " (error)"}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-zinc-500 dark:text-zinc-400">
            No scraper runs recorded yet. Run the scraper to see results here.
          </p>
        )}
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Recent Runs
        </h2>

        {recentRuns.length === 0 ? (
          <p className="text-zinc-500 dark:text-zinc-400">No runs to display.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
                <tr>
                  <th className="whitespace-nowrap px-4 py-3 font-medium text-zinc-600 dark:text-zinc-400">
                    Started
                  </th>
                  <th className="whitespace-nowrap px-4 py-3 font-medium text-zinc-600 dark:text-zinc-400">
                    Finished
                  </th>
                  <th className="whitespace-nowrap px-4 py-3 font-medium text-zinc-600 dark:text-zinc-400">
                    Total Raw
                  </th>
                  <th className="whitespace-nowrap px-4 py-3 font-medium text-zinc-600 dark:text-zinc-400">
                    New Matches
                  </th>
                  <th className="whitespace-nowrap px-4 py-3 font-medium text-zinc-600 dark:text-zinc-400">
                    Spiders
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {recentRuns.map((run, idx) => (
                  <tr key={run.id ?? `run-${idx}`} className="transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-900/50">
                    <td className="whitespace-nowrap px-4 py-3">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      {run.finished_at ? new Date(run.finished_at).toLocaleString() : "Running..."}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{run.total_raw}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-green-600 dark:text-green-400">
                      {run.new_matches}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      {run.spiders?.length ?? 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
