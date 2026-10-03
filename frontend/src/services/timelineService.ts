import type { NeedsConfirmation } from '../api/types';

export const timelineService = {
  async getTimeline(signal?: AbortSignal): Promise<NeedsConfirmation> {
    signal?.throwIfAborted();
    // GET /v1/timeline exists, but neither range filters nor response fields
    // are finalized. Do not issue an unbounded or guessed request.
    return {
      status: 'needs-confirmation',
      message: 'Needs confirmation: timeline time-range filters, activity fields, pagination, and owner access.',
    };
  },
};
