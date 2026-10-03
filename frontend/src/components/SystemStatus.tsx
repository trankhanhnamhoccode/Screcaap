import type { BackendStatus } from '../types';

const labels: Record<BackendStatus, string> = { connected: 'Connected', connecting: 'Connecting', offline: 'Offline', error: 'Error', 'needs-confirmation': 'Needs confirmation' };
export function SystemStatus({ lastCapture, backend, simulated = false }: { lastCapture?: string; backend: BackendStatus; simulated?: boolean }) {
  return <footer className="system-status">
    <span>Last capture: <strong>{lastCapture ? new Date(lastCapture).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : simulated ? 'No captures yet' : 'Unavailable'}</strong></span>
    <span className={`backend-status backend-${backend}`}><span className="status-dot" />Backend: <strong>{labels[backend]}</strong>{simulated && <span className="mock-label">simulated</span>}</span>
  </footer>;
}
