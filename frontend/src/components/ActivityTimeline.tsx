import type { ActivitySegment, ActivityLoadState } from '../types';

export function EmptyState() {
  return <div className="content-state" role="status"><span className="state-symbol" aria-hidden="true">◷</span><h3>No activity recorded yet.</h3><p>Select another day. Recent captures may still be processing.</p></div>;
}
export function LoadingState() {
  return <div className="content-state" role="status"><span className="spinner" aria-hidden="true" /><h3>Loading activity…</h3><p>Getting your activity history.</p></div>;
}
export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div className="content-state" role="alert"><span className="state-symbol" aria-hidden="true">!</span><h3>Unable to load activity.</h3><p>{message}</p><button onClick={onRetry}>Retry</button></div>;
}
function ActivityTimelineItem({ activity }: { activity: ActivitySegment }) {
  const formatTime = (value: string) => new Date(value).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  const icon = activity.application === 'Visual Studio Code' ? '〈〉' : activity.application === 'Google Chrome' ? '◎' : activity.application === 'Slack' ? '#' : '◷';
  return <li className="timeline-item">
    <div className="interval-time" aria-label={`${formatTime(activity.startedAt)} to ${formatTime(activity.endedAt)}`}><time dateTime={activity.startedAt}>{formatTime(activity.startedAt)}</time><span aria-hidden="true">–</span><time dateTime={activity.endedAt}>{formatTime(activity.endedAt)}</time></div>
    <span className="timeline-dot" aria-hidden="true" />
    <article className="activity-card">
      <div className="activity-app"><span className={`app-icon ${activity.application === 'Google Chrome' ? 'browser-icon' : ''}`} aria-hidden="true">{icon}</span><span>{activity.application}</span><span className="interval-label">Inferred interval</span></div>
      <h3>{activity.title}</h3>
      {activity.detail && <p>{activity.detail}</p>}
    </article>
  </li>;
}
export function ActivityTimeline({ state, onRetry }: { state: ActivityLoadState; onRetry: () => void }) {
  if (state.status === 'needs-confirmation') return <div className="content-state" role="status"><h3>Needs confirmation</h3><p>{state.message}</p></div>;
  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState message={state.error.message} onRetry={onRetry} />;
  if (!state.segments.length) return <EmptyState />;
  // Display order is a frontend choice; API ordering remains TODO.
  const sorted = [...state.segments].sort((a, b) => b.startedAt.localeCompare(a.startedAt) || b.id.localeCompare(a.id));
  return <ol className="timeline" aria-label="Inferred activity intervals, newest first">{sorted.map(activity => <ActivityTimelineItem key={activity.id} activity={activity} />)}</ol>;
}
