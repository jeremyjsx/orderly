'use client'

import { useEffect, useRef } from 'react'
import type { Map, Marker } from 'leaflet'

interface Props {
  lat: number
  lng: number
}

type LeafletContainer = HTMLDivElement & { _leaflet_id?: number }

export default function DeliveryMap({ lat, lng }: Props) {
  const containerRef = useRef<LeafletContainer>(null)
  const mapRef = useRef<Map | null>(null)
  const markerRef = useRef<Marker | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    if (containerRef.current._leaflet_id) return  // already initialized
    if (mapRef.current) return

    let cancelled = false

    import('leaflet').then(L => {
      if (cancelled || !containerRef.current) return
      if (containerRef.current._leaflet_id) return  // check again after async gap

      delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
      L.Icon.Default.mergeOptions({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      const map = L.map(containerRef.current!).setView([lat, lng], 15)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
      }).addTo(map)

      const marker = L.marker([lat, lng]).addTo(map)
      marker.bindPopup('Driver location').openPopup()

      mapRef.current = map
      markerRef.current = marker
    })

    return () => {
      cancelled = true
      mapRef.current?.remove()
      mapRef.current = null
      markerRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!mapRef.current || !markerRef.current) return
    markerRef.current.setLatLng([lat, lng])
    mapRef.current.setView([lat, lng], mapRef.current.getZoom())
  }, [lat, lng])

  return <div ref={containerRef} className="w-full h-full" />
}
