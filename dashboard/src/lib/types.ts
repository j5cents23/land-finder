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
  match_score: number | null
  nearest_hospital_miles: number | null
  nearest_bigbox_miles: number | null
  nearest_water_miles: number | null
  nearest_trail_miles: number | null
  nearest_ski_resort_miles: number | null
  county_political_lean: string | null
  county_property_tax_rate: number | null
  school_district_rating: string | null
  avg_annual_snowfall_inches: number | null
  avg_sunny_days: number | null
  county_pop_growth_pct: number | null
  county_median_age: number | null
  county_population: number | null
  county_mil_discount: number | null
}

export interface ListingScores {
  listing_id: string
  nearest_hospital_miles: number | null
  nearest_hospital_name: string | null
  nearest_bigbox_miles: number | null
  nearest_bigbox_name: string | null
  nearest_water_miles: number | null
  nearest_water_type: string | null
  nearest_trail_miles: number | null
  nearest_trail_name: string | null
  nearest_offroad_miles: number | null
  nearest_ski_resort_miles: number | null
  nearest_ski_resort_name: string | null
  nearest_school_miles: number | null
  nearest_school_name: string | null
  school_district_rating: string | null
  county_political_lean: string | null
  county_property_tax_rate: number | null
  county_mil_discount: number | null
  county_population: number | null
  county_pop_growth_pct: number | null
  county_median_age: number | null
  avg_annual_snowfall_inches: number | null
  avg_sunny_days: number | null
  match_score: number | null
  enriched_at: string | null
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
