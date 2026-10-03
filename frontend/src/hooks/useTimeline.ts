import { useEffect, useState } from 'react';
import { apiConfig } from '../api/config';
import { ApiError } from '../services/apiClient';
import { activityService } from '../services/activityService';
import { timelineService } from '../services/timelineService';
import type { ActivityLoadState, DemoScenario } from '../types';

export function useTimeline(date: string, scenario: DemoScenario, retry: number): ActivityLoadState {
  const [state, setState] = useState<ActivityLoadState>({ status: 'loading' });
  useEffect(() => {
    const controller = new AbortController();
    setState({ status: 'loading' });
    async function load() {
      try {
        if (apiConfig.useMocks && scenario === 'loading') return;
        const result: ActivityLoadState = apiConfig.useMocks
          ? { status: 'ready', segments: await activityService.getSegments(date, scenario, controller.signal) }
          : await timelineService.getTimeline(controller.signal);
        if (!controller.signal.aborted) setState(result);
      } catch (error) {
        if (!controller.signal.aborted) setState({
          status: 'error',
          error: {
            kind: error instanceof ApiError ? error.kind : 'backend',
            message: error instanceof ApiError ? error.message : 'Activity history is temporarily unavailable. Please try again.',
          },
        });
      }
    }
    void load();
    return () => controller.abort();
  }, [date, scenario, retry]);
  return state;
}
