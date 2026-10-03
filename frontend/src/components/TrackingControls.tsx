import type { TrackingState } from '../types';

const labels: Record<TrackingState, string> = {
  STOPPED: 'Tracking stopped', STARTING: 'Starting tracking…', RUNNING: 'Tracking active', PAUSED: 'Tracking paused', ERROR: 'Tracking error',
};
export function TrackingControls({ state, onChange }: { state: TrackingState; onChange: (state: TrackingState) => void }) {
  return <div className="tracking-controls">
    <span className={`tracking-status state-${state.toLowerCase()}`} role="status"><span className="status-dot" />{labels[state]}</span>
    {state === 'STOPPED' && <button className="primary" onClick={() => onChange('STARTING')}><span aria-hidden="true">▶</span> Start tracking</button>}
    {state === 'RUNNING' && <button onClick={() => onChange('PAUSED')}><span aria-hidden="true">Ⅱ</span> Pause</button>}
    {state === 'PAUSED' && <button className="primary" onClick={() => onChange('RUNNING')}><span aria-hidden="true">▶</span> Resume</button>}
    {state === 'ERROR' && <button className="primary" onClick={() => onChange('STARTING')}>Try again</button>}
    {state !== 'STOPPED' && <button className="stop-button" onClick={() => onChange('STOPPED')}><span aria-hidden="true">■</span> Stop</button>}
  </div>;
}
