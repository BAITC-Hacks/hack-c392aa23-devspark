import { useEffect, useRef, useState } from 'react'

export function useReducedMotion() {
  const query = '(prefers-reduced-motion: reduce)'
  const [reduced, setReduced] = useState(() => typeof window !== 'undefined' && window.matchMedia(query).matches)
  useEffect(() => {
    const media = window.matchMedia(query)
    const onChange = () => setReduced(media.matches)
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])
  return reduced
}

/** True once the element has scrolled into view (it stays true). */
export function useInView<T extends Element>(threshold = 0.25) {
  const ref = useRef<T | null>(null)
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const element = ref.current
    if (!element || inView) return
    const observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) { setInView(true); observer.disconnect() } }, { threshold })
    observer.observe(element)
    return () => observer.disconnect()
  }, [threshold, inView])
  return [ref, inView] as const
}

/** A clock that runs 0 → duration in a loop while `running`, at ~30 fps. */
export function useLoop(duration: number, running: boolean) {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (!running) return
    let frame = 0
    let last = performance.now()
    let acc = 0
    const tick = (now: number) => {
      acc += now - last
      last = now
      if (acc >= 33) { const step = acc; acc = 0; setElapsed((value) => (value + step) % duration) }
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [duration, running])
  return elapsed
}

/** Animate a number from `from` to `to` once `run` becomes true. */
export function useCountUp(to: number, run: boolean, ms = 1100, from = 0) {
  const reduced = useReducedMotion()
  const [value, setValue] = useState(from)
  useEffect(() => {
    if (!run) { setValue(from); return }
    if (reduced) { setValue(to); return }
    let frame = 0
    const start = performance.now()
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / ms)
      setValue(from + (to - from) * (1 - Math.pow(1 - p, 3)))
      if (p < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [to, from, run, ms, reduced])
  return value
}

export const ease = (p: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, p)), 3)
export const clamp01 = (p: number) => Math.min(1, Math.max(0, p))
