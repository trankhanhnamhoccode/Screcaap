import type { ActivitySegment, DemoScenario, SystemSnapshot } from '../types';

export const demoDate = '2026-10-02';
// Illustrative aggregated intervals, not an aggregation algorithm or wire schema.
// Deliberate gaps remain unassigned. Local timestamps are a demo-only choice.
const mockSegments: ActivitySegment[] = [
  { id: 'segment-001', startedAt: '2026-10-02T22:39:00', endedAt: '2026-10-02T22:41:00', application: 'Visual Studio Code', title: 'Working on frontend implementation', detail: 'screcaap_FE · ActivityTimeline.tsx' },
  { id: 'segment-002', startedAt: '2026-10-02T22:35:00', endedAt: '2026-10-02T22:38:00', application: 'Google Chrome', title: 'Researching React state management', detail: 'Reading documentation' },
  { id: 'segment-003', startedAt: '2026-10-02T22:31:00', endedAt: '2026-10-02T22:34:00', application: 'Visual Studio Code', title: 'Implementing API client', detail: 'Editing frontend service code' },
  { id: 'segment-004', startedAt: '2026-10-02T22:27:00', endedAt: '2026-10-02T22:30:00', application: 'Slack', title: 'Reading project messages', detail: 'Team communication' },
];

export const activityService = {
  async getSegments(date: string, scenario: DemoScenario, signal?: AbortSignal): Promise<ActivitySegment[]> {
    signal?.throwIfAborted();
    await new Promise(resolve => setTimeout(resolve, 450));
    signal?.throwIfAborted();
    if (scenario === 'error') throw new Error('Mock activity loading failure');
    if (date !== demoDate || scenario === 'empty') return [];
    return mockSegments.map(segment => ({ ...segment }));
  },
};

// Separate session metadata; never derive last capture from segment end times.
// Preview changes select independent fixtures, not capture lifecycle transitions.
export const systemService = {
  getSnapshot(scenario: DemoScenario): SystemSnapshot {
    const snapshot: SystemSnapshot = {
      lastCapture: scenario === 'empty' ? undefined : '2026-10-02T22:42:00',
      backend: scenario === 'error' ? 'error' : scenario === 'upload-error' ? 'offline' : scenario === 'loading' ? 'connecting' : 'connected',
    };
    if (scenario === 'pending' || scenario === 'processing' || scenario === 'processing-error') {
      snapshot.captureNotice = {
        kind: 'accepted', status: scenario === 'processing-error' ? 'failed' : scenario,
        error: scenario === 'processing-error' ? { kind: 'backend', message: 'Processing failed for the latest accepted capture. Existing activity history is still available.' } : undefined,
      };
    }
    if (scenario === 'upload-error') {
      snapshot.captureNotice = { kind: 'upload-error', error: { kind: 'network', message: 'The latest capture could not be uploaded. It has not been accepted for processing.' } };
    }
    return snapshot;
  },
};
