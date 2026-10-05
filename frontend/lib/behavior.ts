// Client-side behavior-event batching.
//
// Per the design, we track MEANINGFUL learning events and flush them in
// batches (e.g. on run/submit), never per keystroke. This buffer accumulates
// events and exposes a flush that posts them in one request.

import { api } from "@/lib/api/endpoints";
import type { EventRecordRequest, BehaviorEventType } from "@/types/profile";

export class BehaviorBuffer {
  private queue: EventRecordRequest[] = [];

  constructor(
    private readonly userId: string,
    private readonly sessionId?: string,
  ) {}

  /** Queue a meaningful event (does not hit the network). */
  add(
    eventType: BehaviorEventType,
    fields: Partial<Omit<EventRecordRequest, "user_id" | "event_type">> = {},
  ): void {
    this.queue.push({
      user_id: this.userId,
      session_id: this.sessionId,
      event_type: eventType,
      ...fields,
    });
  }

  /** Number of events waiting to be sent. */
  get pending(): number {
    return this.queue.length;
  }

  /** Send all queued events in one batch and clear the buffer. */
  async flush(): Promise<number> {
    if (this.queue.length === 0) return 0;
    const batch = this.queue;
    this.queue = [];
    try {
      const res = await api.recordEvents(batch);
      return res.recorded;
    } catch {
      // On failure, requeue so events aren't silently lost.
      this.queue = batch.concat(this.queue);
      return 0;
    }
  }
}
