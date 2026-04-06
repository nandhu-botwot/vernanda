"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCallStatus } from "@/lib/api";
import type { CallStatus } from "@/lib/types";

const PIPELINE_STAGES: { status: CallStatus; label: string }[] = [
  { status: "UPLOADED", label: "Uploaded" },
  { status: "PREPROCESSING", label: "Preprocessing Audio" },
  { status: "TRANSCRIBING", label: "Transcribing & Diarizing" },
  { status: "EVALUATING", label: "Evaluating Quality" },
  { status: "COMPLETED", label: "Report Ready" },
];

interface CallStatusTrackerProps {
  callId: string;
  initialStatus: CallStatus;
}

export default function CallStatusTracker({ callId, initialStatus }: CallStatusTrackerProps) {
  const router = useRouter();
  const [status, setStatus] = useState<CallStatus>(initialStatus);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "COMPLETED" || status === "FAILED") return;

    const interval = setInterval(async () => {
      try {
        const data = await getCallStatus(callId);
        setStatus(data.status as CallStatus);
        if (data.error_message) setError(data.error_message);
        if (data.status === "COMPLETED") {
          clearInterval(interval);
          router.push(`/reports/${callId}`);
        }
      } catch {
        // Polling error (backend busy processing) — keep trying
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [callId, status, router]);

  const currentIdx = PIPELINE_STAGES.findIndex((s) => s.status === status);
  const isFailed = status === "FAILED";

  return (
    <div className="max-w-lg mx-auto">
      <div className="space-y-4">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isDone = idx < currentIdx || status === "COMPLETED";
          const isActive = idx === currentIdx && !isFailed;
          const isPending = idx > currentIdx;

          return (
            <div key={stage.status} className="flex items-center gap-4">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-colors ${
                  isDone
                    ? "bg-emerald-500 text-white"
                    : isActive
                    ? "bg-blue-500 text-white animate-pulse"
                    : isFailed && idx === currentIdx
                    ? "bg-red-500 text-white"
                    : "bg-gray-200 text-gray-400"
                }`}
              >
                {isDone ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : isFailed && idx === currentIdx ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <span className="text-xs font-bold">{idx + 1}</span>
                )}
              </div>
              <span
                className={`text-sm ${
                  isDone ? "text-emerald-700 font-medium" : isActive ? "text-blue-700 font-medium" : "text-gray-400"
                }`}
              >
                {stage.label}
                {isActive && !isFailed && <span className="ml-2 text-blue-400">Processing...</span>}
              </span>
            </div>
          );
        })}
      </div>

      {isFailed && error && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-medium text-red-800">Processing Failed</p>
          <p className="text-sm text-red-600 mt-1">{error}</p>
        </div>
      )}
    </div>
  );
}
