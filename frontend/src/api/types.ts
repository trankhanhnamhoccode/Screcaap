// Only this enum has a finalized representation in docs/api-contract.md.
export type CaptureProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

// Frontend readiness state, NOT a backend response envelope.
export interface NeedsConfirmation {
  status: 'needs-confirmation';
  message: string;
}

// Needs confirmation: capture upload encoding, metadata field names, response
// envelopes, timeline query/segment/pagination fields, OCR schema, image delivery,
// and authentication. No DTOs can be defined accurately until these are settled.
