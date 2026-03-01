export interface Listing {
  id: string
  source: string
  source_id: string
  url: string
  title: string
  description: string | null
  price: number
  acreage: number
  price_per_acre: number
  address: string
  city: string
  county: string
  state: string
  zip_code: string
  latitude: number | null
  longitude: number | null
  zoning: string | null
  has_water: number | null
  has_utilities: number | null
  has_road_access: number | null
  image_urls: string
  first_seen_at: string
  last_seen_at: string
  is_active: number
  is_favorited: number
}

export interface SearchCriteria {
  id: string
  name: string
  min_acreage: number | null
  max_price: number | null
  max_ppa: number | null
  states: string
  counties: string
  center_lat: number | null
  center_lng: number | null
  radius_miles: number | null
  require_water: number
  require_utils: number
  require_road: number
  zoning_types: string
  is_active: number
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}
