import type { CaptureNotice } from '../types';

export function CaptureStatus({ notice }: { notice?: CaptureNotice }) {
  if (!notice) return null;
  if (notice.kind === 'upload-error') {
    return <div className="error-banner" role="alert"><strong>Upload failed. </strong>{notice.error.message}</div>;
  }
  if (notice.status === 'failed') {
    return <div className="error-banner" role="alert"><strong>Capture processing failed. </strong>{notice.error?.message ?? 'The accepted capture could not be processed.'} It will not retry automatically.</div>;
  }
  return <div className="session-notice" role="status"><span className="status-dot" /><p>{notice.status === 'pending' ? 'Capture accepted · Pending processing.' : notice.status === 'processing' ? 'Capture accepted · Processing.' : 'Capture processing completed.'} Recent captures may not yet appear in the timeline.</p></div>;
}
