import { useState } from 'react'
import { ChevronLeft, ChevronRight, Maximize2 } from 'lucide-react'
import Lightbox from 'yet-another-react-lightbox'
import Zoom from 'yet-another-react-lightbox/plugins/zoom'
import 'yet-another-react-lightbox/styles.css'

const THUMBS = 3

export default function PostGallery({ images }: { images: string[] }) {
  const [idx, setIdx] = useState(0)
  const [thumbStart, setThumbStart] = useState(0)
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [broken, setBroken] = useState<Set<string>>(new Set())

  const valid = images.filter(u => !broken.has(u))
  if (valid.length === 0) return null

  const safeIdx = Math.max(0, Math.min(idx, valid.length - 1))
  const mainUrl = valid[safeIdx]
  const maxThumbStart = Math.max(0, valid.length - THUMBS)
  const thumbIndices = Array.from({ length: THUMBS }, (_, i) => thumbStart + i).filter(i => i < valid.length)

  const goTo = (next: number) => {
    const clamped = Math.max(0, Math.min(next, valid.length - 1))
    setIdx(clamped)
    // Auto-scroll thumbnail window to keep active thumb visible
    if (clamped < thumbStart) setThumbStart(Math.max(0, clamped))
    else if (clamped >= thumbStart + THUMBS) setThumbStart(Math.min(clamped - THUMBS + 1, maxThumbStart))
  }

  const markBroken = (url: string) => setBroken(prev => new Set([...prev, url]))

  return (
    <div className="my-10">
      <h2 className="text-xl font-semibold text-text-primary mb-4">Gallery</h2>

      {/* ── Line 1: Main image ─────────────────────────────────────────────── */}
      <div className="relative rounded-2xl overflow-hidden bg-bg-secondary border border-border mb-3 group">
        <img
          key={mainUrl}
          src={mainUrl}
          alt={`Gallery image ${safeIdx + 1}`}
          loading="lazy"
          onClick={() => setLightboxOpen(true)}
          onError={() => markBroken(mainUrl)}
          className="w-full h-72 sm:h-[26rem] object-contain cursor-zoom-in transition-transform duration-300 group-hover:scale-[1.01]"
        />

        {/* Zoom hint */}
        <button
          onClick={() => setLightboxOpen(true)}
          className="absolute top-3 right-3 p-2 bg-black/60 rounded-lg text-white opacity-0 group-hover:opacity-100 hover:bg-black/80 transition-all duration-200"
          title="Open fullscreen"
        >
          <Maximize2 className="w-4 h-4" />
        </button>

        {/* Counter */}
        {valid.length > 1 && (
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-black/60 rounded-full text-white text-xs font-medium pointer-events-none">
            {safeIdx + 1} / {valid.length}
          </div>
        )}

        {/* Prev / Next on main */}
        {valid.length > 1 && (
          <>
            <button
              onClick={() => goTo(safeIdx - 1)}
              disabled={safeIdx === 0}
              className="absolute left-3 top-1/2 -translate-y-1/2 p-2.5 bg-black/60 rounded-full text-white hover:bg-black/80 disabled:opacity-20 disabled:cursor-not-allowed transition-all duration-200 opacity-0 group-hover:opacity-100"
              aria-label="Previous image"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => goTo(safeIdx + 1)}
              disabled={safeIdx === valid.length - 1}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-black/60 rounded-full text-white hover:bg-black/80 disabled:opacity-20 disabled:cursor-not-allowed transition-all duration-200 opacity-0 group-hover:opacity-100"
              aria-label="Next image"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </>
        )}
      </div>

      {/* ── Line 2: Thumbnails ─────────────────────────────────────────────── */}
      {valid.length > 1 && (
        <div className="flex items-stretch gap-2">
          {/* Prev thumbnails */}
          <button
            onClick={() => setThumbStart(prev => Math.max(0, prev - THUMBS))}
            disabled={thumbStart === 0}
            className="flex-shrink-0 w-8 flex items-center justify-center rounded-xl border border-border text-text-muted hover:text-accent hover:border-accent/40 hover:bg-accent/5 disabled:opacity-20 disabled:cursor-not-allowed transition-all duration-200"
            aria-label="Previous thumbnails"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {/* Thumb images */}
          <div className="flex gap-2 flex-1">
            {thumbIndices.map(i => (
              <button
                key={i}
                onClick={() => goTo(i)}
                className={`flex-1 rounded-xl overflow-hidden border-2 transition-all duration-200 focus:outline-none ${
                  i === safeIdx
                    ? 'border-accent shadow-md shadow-accent/30 scale-[1.03]'
                    : 'border-border hover:border-accent/50 hover:scale-[1.02]'
                }`}
                aria-label={`View image ${i + 1}`}
              >
                <img
                  src={valid[i]}
                  alt={`Thumbnail ${i + 1}`}
                  loading="lazy"
                  className="w-full h-20 object-cover"
                  onError={() => markBroken(valid[i])}
                />
              </button>
            ))}
            {/* Fill empty slots so layout stays stable */}
            {thumbIndices.length < THUMBS && Array.from({ length: THUMBS - thumbIndices.length }).map((_, k) => (
              <div key={`empty-${k}`} className="flex-1" />
            ))}
          </div>

          {/* Next thumbnails */}
          <button
            onClick={() => setThumbStart(prev => Math.min(prev + THUMBS, maxThumbStart))}
            disabled={thumbStart >= maxThumbStart}
            className="flex-shrink-0 w-8 flex items-center justify-center rounded-xl border border-border text-text-muted hover:text-accent hover:border-accent/40 hover:bg-accent/5 disabled:opacity-20 disabled:cursor-not-allowed transition-all duration-200"
            aria-label="Next thumbnails"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Lightbox ───────────────────────────────────────────────────────── */}
      <Lightbox
        open={lightboxOpen}
        close={() => setLightboxOpen(false)}
        index={safeIdx}
        slides={valid.map(src => ({ src }))}
        plugins={[Zoom]}
        on={{ view: ({ index }) => setIdx(index) }}
        zoom={{ maxZoomPixelRatio: 4, scrollToZoom: true }}
        styles={{ container: { backgroundColor: 'rgba(15,23,42,0.96)' } }}
      />
    </div>
  )
}
