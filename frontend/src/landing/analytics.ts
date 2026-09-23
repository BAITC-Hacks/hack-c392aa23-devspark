// Two events only, no third-party trackers: the landing reports to our own API.
export type LandingEvent = 'demo_opened' | 'contact_clicked'

export function track(event: LandingEvent, detail: { profile?: string; lang?: string } = {}) {
  const body = JSON.stringify({ event, ...detail })
  try {
    if (navigator.sendBeacon) { navigator.sendBeacon('/api/landing/events', new Blob([body], { type: 'application/json' })); return }
    void fetch('/api/landing/events', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true }).catch(() => undefined)
  } catch { /* analytics must never break the page */ }
}
