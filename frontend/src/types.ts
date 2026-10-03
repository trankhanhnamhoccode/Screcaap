// UI models only; these are not the backend transport contract.
import type { NeedsConfirmation } from './api/types';
export type { CaptureProcessingStatus } from './api/types';
import type { CaptureProcessingStatus } from './api/types';
export type TrackingState = 'STOPPED' | 'STARTING' | 'RUNNING' | 'PAUSED' | 'ERROR';
export type BackendStatus = 'connected' | 'connecting' | 'offline' | 'error' | 'needs-confirmation';
export type FailureKind = 'capture' | 'permission' | 'network' | 'timeout' | 'backend' | 'invalid-response';
export interface UiError { kind: FailureKind; message: string }
export interface ActivitySegment {
  id: string;
  startedAt: string;
  endedAt: string;
  application: string;
  title: string;
  detail?: string;
}
export type CaptureNotice =
  | { kind: 'accepted'; status: CaptureProcessingStatus; error?: UiError }
  | { kind: 'upload-error'; error: UiError };
export interface SystemSnapshot {
  lastCapture?: string;
  backend: BackendStatus;
  captureNotice?: CaptureNotice;
}
export type ActivityLoadState =
  | NeedsConfirmation
  | { status: 'loading' }
  | { status: 'ready'; segments: ActivitySegment[] }
  | { status: 'error'; error: UiError };
export type DemoScenario = 'normal' | 'empty' | 'loading' | 'error' | 'pending' | 'processing' | 'processing-error' | 'upload-error' | 'permission-error';
