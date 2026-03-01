"use client"

import { useEffect, useState } from "react"
import dynamic from "next/dynamic"
import type { Listing } from "@/lib/types"
import { formatPrice } from "@/lib/format"

const MapContainer = dynamic(
  () => import("react-leaflet").then(m => m.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import("react-leaflet").then(m => m.TileLayer),
  { ssr: false }
)
const CircleMarker = dynamic(
  () => import("react-leaflet").then(m => m.CircleMarker),
  { ssr: false }
)
const Popup = dynamic(
  () => import("react-leaflet").then(m => m.Popup),
  { ssr: false }
)

const LEAFLET_CSS_URL = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"

interface ListingMapProps {
  readonly listings: Listing[]
}

function getMarkerColor(listing: Listing): string {
  const twentyFourHoursAgo = Date.now() - 24 * 60 * 60 * 1000
  const firstSeen = new Date(listing.first_seen_at).getTime()

  if (listing.price_per_acre < 200000) return "#ef4444"
  if (firstSeen > twentyFourHoursAgo) return "#22c55e"
  return "#3b82f6"
}

export default function ListingMap({ listings }: ListingMapProps) {
  const [cssLoaded, setCssLoaded] = useState(false)

  useEffect(() => {
    if (document.querySelector(`link[href="${LEAFLET_CSS_URL}"]`)) {
      setCssLoaded(true)
      return
    }
    const link = document.createElement("link")
    link.rel = "stylesheet"
    link.href = LEAFLET_CSS_URL
    link.onload = () => setCssLoaded(true)
    document.head.appendChild(link)
  }, [])

  const geoListings = listings.filter(
    l => l.latitude !== null && l.longitude !== null
  )

  if (!cssLoaded) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
        <p className="text-zinc-500 dark:text-zinc-400">Loading map...</p>
      </div>
    )
  }

  if (geoListings.length === 0) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
        <p className="text-zinc-500 dark:text-zinc-400">No listings with location data</p>
      </div>
    )
  }

  const avgLat = geoListings.reduce((sum, l) => sum + (l.latitude ?? 0), 0) / geoListings.length
  const avgLng = geoListings.reduce((sum, l) => sum + (l.longitude ?? 0), 0) / geoListings.length

  return (
    <MapContainer
      center={[avgLat, avgLng]}
      zoom={6}
      className="h-full w-full rounded-lg"
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {geoListings.map(listing => (
        <CircleMarker
          key={listing.id}
          center={[listing.latitude as number, listing.longitude as number]}
          radius={8}
          pathOptions={{
            fillColor: getMarkerColor(listing),
            fillOpacity: 0.8,
            color: "#fff",
            weight: 2,
          }}
        >
          <Popup>
            <div className="text-sm">
              <p className="font-semibold">{listing.title}</p>
              <p>{formatPrice(listing.price)} &middot; {listing.acreage.toFixed(1)} ac</p>
              <a
                href={`/listings/${listing.id}`}
                className="text-blue-600 underline"
              >
                View details
              </a>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
