import { type RefObject, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { clamp01 } from './hooks'

const NODES = [
  { id: 'junior', label: 'JUNIOR' },
  { id: 'middle', label: 'MIDDLE' },
  { id: 'senior', label: 'SENIOR' },
  { id: 'lead', label: 'LEAD' },
]

type Geometry = { x: number; height: number; d: string; nodes: { id: string; label: string; y: number }[] }

/**
 * The page's spine: a mint line that draws itself as you scroll, passing through the
 * four grade nodes that anchor the main sections — the product's grade ladder,
 * turned into the page layout. Decorative, so it is hidden from assistive tech.
 */
export function Path({ wrapperRef, deps }: { wrapperRef: RefObject<HTMLDivElement>; deps: unknown[] }) {
  const [geo, setGeo] = useState<Geometry | null>(null)
  const [drawn, setDrawn] = useState(0)
  const [length, setLength] = useState(0)
  const drawRef = useRef<SVGPathElement>(null)

  useEffect(() => {
    const wrapper = wrapperRef.current
    if (!wrapper) return
    const measure = () => {
      const box = wrapper.getBoundingClientRect()
      const container = wrapper.querySelector('.lp-container')
      const x = (container ? container.getBoundingClientRect().left - box.left : 0) + 48
      const height = wrapper.scrollHeight
      const nodes = NODES.map((node) => {
        const section = document.getElementById(node.id)
        return { ...node, y: section ? section.getBoundingClientRect().top - box.top + 104 : 0 }
      })
      const points = [0, ...nodes.map((node) => node.y), height - 24]
      let d = `M ${x} ${points[0]}`
      for (let i = 1; i < points.length; i += 1) {
        const [y0, y1] = [points[i - 1], points[i]]
        const bend = i % 2 ? 22 : -22
        d += ` C ${x + bend} ${y0 + (y1 - y0) * 0.35}, ${x - bend} ${y0 + (y1 - y0) * 0.65}, ${x} ${y1}`
      }
      setGeo({ x, height, d, nodes })
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(wrapper)
    window.addEventListener('resize', measure)
    return () => { observer.disconnect(); window.removeEventListener('resize', measure) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wrapperRef, ...deps])

  useLayoutEffect(() => { if (drawRef.current) setLength(drawRef.current.getTotalLength()) }, [geo?.d])

  useEffect(() => {
    const wrapper = wrapperRef.current
    if (!wrapper) return
    let frame = 0
    const update = () => {
      frame = 0
      const box = wrapper.getBoundingClientRect()
      setDrawn(window.innerHeight * 0.62 - box.top)
    }
    const onScroll = () => { if (!frame) frame = requestAnimationFrame(update) }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => { window.removeEventListener('scroll', onScroll); cancelAnimationFrame(frame) }
  }, [wrapperRef])

  if (!geo) return null
  const progress = clamp01(drawn / geo.height)
  return (
    <svg className="lp-path" height={geo.height} aria-hidden="true" focusable="false">
      <path className="rail" d={geo.d} />
      <path ref={drawRef} className="draw" d={geo.d} style={{ strokeDasharray: length || undefined, strokeDashoffset: length ? length * (1 - progress) : undefined }} />
      {geo.nodes.map((node) => {
        const lit = drawn >= node.y
        return (
          <g key={node.id} className={`lp-node ${lit ? 'is-lit' : ''}`}>
            <circle cx={geo.x} cy={node.y} r={lit ? 8 : 6} fill={lit ? 'var(--lp-mint)' : 'var(--lp-surface)'} stroke={lit ? 'var(--lp-pine)' : 'var(--lp-line)'} strokeWidth={2} />
            <text x={geo.x} y={node.y - 18} textAnchor="middle">{node.label}</text>
          </g>
        )
      })}
    </svg>
  )
}
