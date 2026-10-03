import { useEffect, useState } from 'react';
import { ActivityTimeline } from './components/ActivityTimeline';
import { CaptureStatus } from './components/CaptureStatus';
import { SystemStatus } from './components/SystemStatus';
import { TrackingControls } from './components/TrackingControls';
import { demoDate, systemService } from './services/activityService';
import { apiConfig } from './api/config';
import { useTimeline } from './hooks/useTimeline';
import { captureService } from './services/captureService';
import { healthService } from './services/healthService';
import type { DemoScenario, TrackingState, UiError } from './types';

const trackingDescriptions: Record<TrackingState, string> = {
  STOPPED: 'Tracking is stopped. Start when you’re ready.', STARTING: 'Preparing your local tracking session…', RUNNING: 'Local tracking controls are active. No screenshots are being captured.', PAUSED: 'Tracking is paused. Resume only when you’re ready.', ERROR: 'Tracking needs your attention. It will not restart automatically.',
};
function dateKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
export default function App() {
  const [tracking, setTracking] = useState<TrackingState>('STOPPED');
  const [date, setDate] = useState(apiConfig.useMocks ? new Date(`${demoDate}T12:00:00`) : new Date());
  const [scenario, setScenario] = useState<DemoScenario>('normal');
  const [retry, setRetry] = useState(0);
  const [trackingError, setTrackingError] = useState<UiError>();
  const system = apiConfig.useMocks ? systemService.getSnapshot(scenario) : undefined;
  const loadState = useTimeline(dateKey(date), scenario, retry);
  const health = healthService.getReadiness();
  const capture = captureService.getReadiness();

  useEffect(() => {
    if (tracking !== 'STARTING') return;
    const timer = window.setTimeout(() => {
      if (apiConfig.useMocks && scenario === 'permission-error') {
        setTrackingError({ kind: 'permission', message: 'Screen capture permission was denied. Allow access before trying again.' });
        setTracking('ERROR');
      } else setTracking('RUNNING');
    }, 600);
    return () => window.clearTimeout(timer);
  }, [tracking, scenario]);

  function changeTracking(next: TrackingState) {
    setTrackingError(undefined);
    setTracking(next);
  }
  function moveDate(offset: number) {
    setDate(current => { const next = new Date(current); next.setDate(next.getDate() + offset); return next; });
  }
  const count = loadState.status === 'ready' ? loadState.segments.length : undefined;
  return <div className="app-shell">
    <header className="app-header"><a className="brand" href="./"><span className="brand-mark" aria-hidden="true"><span /><span /><span /></span>Screcaap</a><TrackingControls state={tracking} onChange={changeTracking} /></header>
    <main>
      <div className="page-heading"><div><div className="eyebrow">YOUR WORKDAY, AT A GLANCE</div><h1>Activity</h1><p>Little moments. A clearer picture of your day.</p></div><span className="demo-badge">{apiConfig.useMocks ? 'Local demo' : 'API integration'}</span></div>
      <div className={`session-notice notice-${tracking.toLowerCase()}`}><span className="status-dot" /><p>{trackingDescriptions[tracking]}</p></div>
      {trackingError && <div className="error-banner" role="alert">{trackingError.message}</div>}
      <CaptureStatus notice={system?.captureNotice} />
      {!apiConfig.useMocks && <div className="session-notice" role="status"><p>{capture.message}</p></div>}
      <section className="timeline-panel" aria-labelledby="timeline-heading">
        <div className="timeline-heading"><div><h2 id="timeline-heading">{date.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })}</h2><span>{date.getFullYear()} <span aria-hidden="true">·</span> {count === undefined ? 'Activity history' : `${count} activity intervals`} <span aria-hidden="true">·</span> Newest first</span></div><div className="date-navigation"><button aria-label="Previous day" onClick={() => moveDate(-1)}>‹</button><button onClick={() => setDate(apiConfig.useMocks ? new Date(`${demoDate}T12:00:00`) : new Date())}>{apiConfig.useMocks ? 'Demo day' : 'Today'}</button><button aria-label="Next day" onClick={() => moveDate(1)}>›</button></div></div>
        <ActivityTimeline state={loadState} onRetry={() => { setScenario('normal'); setRetry(value => value + 1); }} />
        <div className="timeline-note"><span aria-hidden="true">◈</span> Intervals are inferred from multiple observations. Unsampled gaps do not guarantee continuous activity. Recent captures may not appear yet.</div>
      </section>
      <SystemStatus lastCapture={system?.lastCapture} backend={system?.backend ?? health.status} simulated={apiConfig.useMocks} />
      {!apiConfig.useMocks && <p className="demo-settings">{health.message}</p>}
      {apiConfig.useMocks && <details className="demo-settings"><summary>Demo preview settings</summary><div><label htmlFor="scenario">Preview state</label><select id="scenario" value={scenario} onChange={event => setScenario(event.target.value as DemoScenario)}><option value="normal">Activity timeline</option><option value="empty">Empty history</option><option value="loading">Loading history</option><option value="error">History load error</option><option value="pending">Accepted capture pending</option><option value="processing">Accepted capture processing</option><option value="processing-error">Capture processing failed</option><option value="upload-error">Upload / network error</option><option value="permission-error">Permission denied on Start</option></select><p>Mock data and connection status. Tracking controls update local state only.</p></div></details>}
    </main>
  </div>;
}
