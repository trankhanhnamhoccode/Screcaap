import type { NeedsConfirmation } from '../api/types';

export const captureService = {
  getReadiness(): NeedsConfirmation {
    return {
      status: 'needs-confirmation',
      message: 'Needs confirmation: capture upload format, metadata, response fields, and owner access. Screenshots are not being captured or uploaded.',
    };
  },
};
// No upload or polling methods until request encoding and response fields are
// finalized. A 202 is acceptance only; failed processing is not upload failure.
