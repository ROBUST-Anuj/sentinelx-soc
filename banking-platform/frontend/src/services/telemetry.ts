/**
 * NexaBank Client-side Behavioural Telemetry Collector.
 * Privacy-preserving passive monitoring of DOM & browser events:
 * - Tab visibility (Page Visibility API)
 * - Window blur and focus
 * - Fullscreen changes during verification
 * - Rapid paste attempts (metadata count only, never content)
 * - Excessive page interaction bursts
 */

import { api } from './api';

class BrowserTelemetryCollector {
  private sessionId: string;
  private tabSwitchCount: number = 0;
  private lastBlurTimestamp: number = 0;
  private pasteCount: number = 0;
  private isCollecting: boolean = false;
  private activeTxId: string | null = null;

  constructor() {
    this.sessionId = `sess-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }

  public setActiveTransaction(txId: string | null) {
    this.activeTxId = txId;
  }

  public init() {
    if (this.isCollecting || typeof window === 'undefined') return;
    this.isCollecting = true;

    // 1. Tab Visibility API (Tab switching)
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.tabSwitchCount++;
        // If user is switching tabs during active payment / OTP verification
        if (this.tabSwitchCount >= 3) {
          this.emitTelemetry('TAB_SWITCH_BURST', 'browser_behaviour', {
            tab_switch_count: this.tabSwitchCount,
            state: 'hidden',
          });
        }
      }
    });

    // 2. Window Blur (Losing window focus)
    window.addEventListener('blur', () => {
      this.lastBlurTimestamp = Date.now();
      if (this.activeTxId) {
        this.emitTelemetry('WINDOW_BLUR_DURING_TRANSACTION', 'browser_behaviour', {
          transaction_id: this.activeTxId,
        });
      }
    });

    // 3. Fullscreen Exit
    document.addEventListener('fullscreenchange', () => {
      if (!document.fullscreenElement && this.activeTxId) {
        this.emitTelemetry('FULLSCREEN_EXIT_DURING_OTP', 'browser_behaviour', {
          transaction_id: this.activeTxId,
        });
      }
    });

    // 4. Repeated Paste in Sensitive Fields (Counts only, zero clipboard access)
    document.addEventListener('paste', (e) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === 'INPUT' || target.getAttribute('role') === 'textbox')) {
        this.pasteCount++;
        if (this.pasteCount >= 3) {
          this.emitTelemetry('REPEATED_PASTE_ATTEMPT', 'browser_behaviour', {
            paste_count: this.pasteCount,
            field_name: target.getAttribute('name') || target.getAttribute('placeholder') || 'input',
          });
        }
      }
    });
  }

  public async emitTelemetry(
    eventType: string,
    category: string,
    metadata: Record<string, any> = {},
    isSimulation: boolean = false
  ) {
    try {
      await api.submitTelemetry({
        event_type: eventType,
        category: category,
        session_id: this.sessionId,
        transaction_id: this.activeTxId || metadata.transaction_id,
        device_id: navigator.userAgent.slice(0, 50),
        source_application: 'NexaBank-Web',
        event_metadata: metadata,
        is_simulation: isSimulation,
      });
    } catch (err) {
      // Non-blocking passive telemetry: failure must never disrupt banking UX
      console.debug('Telemetry delivery skipped:', err);
    }
  }
}

export const telemetry = new BrowserTelemetryCollector();
