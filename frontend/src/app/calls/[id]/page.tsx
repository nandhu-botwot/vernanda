"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getCall, retryCall } from "@/lib/api";
import { Button } from "@/components/ui/button";
import CallStatusTracker from "@/components/call-status-tracker";
import TranscriptViewer from "@/components/transcript-viewer";
import type { Call, CallStatus } from "@/lib/types";
import { formatDate, formatDuration, statusColor, statusLabel } from "@/lib/utils";

export default function CallDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [call, setCall] = useState<Call | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getCall(id);
        setCall(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load call");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) return <p className="text-gray-400">Loading...</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!call) return <p className="text-gray-400">Call not found.</p>;

  const isProcessing = !["COMPLETED", "FAILED"].includes(call.status);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{call.filename}</h1>
          <p className="text-gray-500 mt-1">
            {call.agent_name && `Agent: ${call.agent_name} | `}
            Duration: {formatDuration(call.duration_seconds)} | Uploaded: {formatDate(call.created_at)}
          </p>
        </div>
        <div className="flex gap-2">
          {call.status === "COMPLETED" && (
            <Link href={`/reports/${call.id}`}>
              <Button>View Report</Button>
            </Link>
          )}
          {call.status === "FAILED" && (
            <Button
              variant="outline"
              onClick={async () => {
                try {
                  await retryCall(call.id);
                  window.location.reload();
                } catch {}
              }}
            >
              Retry
            </Button>
          )}
        </div>
      </div>

      {/* Status & Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Call Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Status</span>
              <Badge className={statusColor(call.status)}>{statusLabel(call.status)}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Language</span>
              <span>{call.call_language.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Call Type</span>
              <span>{call.call_type || "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">File Size</span>
              <span>{(call.file_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">STT Engine</span>
              <span>{call.stt_engine_used || "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Confidence</span>
              <span>{call.whisper_confidence != null ? `${(call.whisper_confidence * 100).toFixed(0)}%` : "-"}</span>
            </div>
          </CardContent>
        </Card>

        {/* Pipeline progress */}
        {isProcessing && (
          <Card>
            <CardHeader>
              <CardTitle>Processing Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <CallStatusTracker callId={call.id} initialStatus={call.status as CallStatus} />
            </CardContent>
          </Card>
        )}
      </div>

      {/* Transcript */}
      {call.transcript && (
        <Card>
          <CardHeader>
            <CardTitle>Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            <TranscriptViewer transcript={call.transcript} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
