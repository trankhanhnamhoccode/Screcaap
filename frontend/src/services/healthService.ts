import type { NeedsConfirmation } from '../api/types';

export const healthService = {
  getReadiness(): NeedsConfirmation {
    return {
      status: 'needs-confirmation',
      message: 'Needs confirmation: docs/api-contract.md does not define a health/status endpoint.',
    };
  },
};
