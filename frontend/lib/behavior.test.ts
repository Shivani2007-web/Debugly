// Tests for the client-side behavior buffer (batched, not per-keystroke).

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { BehaviorBuffer } from "./behavior";
import { api } from "@/lib/api/endpoints";

describe("BehaviorBuffer", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("queues events without sending", () => {
    const buf = new BehaviorBuffer("u1", "s1");
    buf.add("submission", { concept_key: "loops" });
    buf.add("runtime_error", { concept_key: "loops", error_type: "IndexError" });
    expect(buf.pending).toBe(2);
  });

  it("flushes all queued events in ONE batch call", async () => {
    const spy = vi
      .spyOn(api, "recordEvents")
      .mockResolvedValue({ recorded: 2, total_events: 2 });
    const buf = new BehaviorBuffer("u1");
    buf.add("submission", { concept_key: "loops" });
    buf.add("successful_execution", { concept_key: "loops" });

    const sent = await buf.flush();

    expect(spy).toHaveBeenCalledTimes(1); // batched, single request
    expect(sent).toBe(2);
    expect(buf.pending).toBe(0);
  });

  it("flush with empty queue is a no-op", async () => {
    const spy = vi.spyOn(api, "recordEvents");
    const buf = new BehaviorBuffer("u1");
    const sent = await buf.flush();
    expect(sent).toBe(0);
    expect(spy).not.toHaveBeenCalled();
  });

  it("requeues events if the flush fails (no silent loss)", async () => {
    vi.spyOn(api, "recordEvents").mockRejectedValue(new Error("network"));
    const buf = new BehaviorBuffer("u1");
    buf.add("submission", { concept_key: "loops" });
    const sent = await buf.flush();
    expect(sent).toBe(0);
    expect(buf.pending).toBe(1); // preserved for retry
  });

  it("attaches user_id and session_id to each event", async () => {
    let captured: unknown;
    vi.spyOn(api, "recordEvents").mockImplementation(async (events) => {
      captured = events;
      return { recorded: events.length, total_events: events.length };
    });
    const buf = new BehaviorBuffer("student-7", "sess-9");
    buf.add("hint_requested", { concept_key: "list_indexing" });
    await buf.flush();
    expect(captured).toEqual([
      {
        user_id: "student-7",
        session_id: "sess-9",
        event_type: "hint_requested",
        concept_key: "list_indexing",
      },
    ]);
  });
});
