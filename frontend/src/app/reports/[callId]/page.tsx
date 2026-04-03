"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { getReport, getCall } from "@/lib/api";
import ScoreGauge from "@/components/score-gauge";
import ScoreCard from "@/components/score-card";
import TranscriptViewer from "@/components/transcript-viewer";
import type { QAReport, Call } from "@/lib/types";
import { formatDate, formatDuration } from "@/lib/utils";

export default function ReportPage({ params }: { params: Promise<{ callId: string }> }) {
  const { callId } = use(params);
  const [report, setReport] = useState<QAReport | null>(null);
  const [call, setCall] = useState<Call | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [r, c] = await Promise.all([getReport(callId), getCall(callId)]);
        setReport(r);
        setCall(c);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load report");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [callId]);

  if (loading) return <p className="text-gray-400">Loading report...</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!report || !call) return <p className="text-gray-400">Report not found.</p>;

  const scoreEntries = Object.entries(report.scores);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">QA Report</h1>
          <p className="text-gray-500 mt-1">
            {call.filename} | Agent: {call.agent_name || "Unknown"} |{" "}
            {formatDuration(call.duration_seconds)} | {formatDate(call.created_at)}
          </p>
        </div>
        <Link href={`/calls/${callId}`} className="text-sm text-blue-600 hover:underline">
          View Call Details
        </Link>
      </div>

      {/* Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-1">
          <CardContent className="pt-6 flex justify-center">
            <div className="relative">
              <ScoreGauge score={report.total_score} grade={report.grade} size="lg" />
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {report.call_summary && (
              <p className="text-sm text-gray-700">{report.call_summary}</p>
            )}
            <Separator />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-emerald-700 mb-2">Strengths</h4>
                {report.strengths && report.strengths.length > 0 ? (
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {report.strengths.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-400">None identified</p>
                )}
              </div>
              <div>
                <h4 className="font-medium text-red-700 mb-2">Areas for Improvement</h4>
                {report.weaknesses && report.weaknesses.length > 0 ? (
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {report.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-400">None identified</p>
                )}
              </div>
            </div>
            {report.critical_issues && report.critical_issues.length > 0 && (
              <>
                <Separator />
                <div>
                  <h4 className="font-medium text-red-800 mb-2">Critical Issues</h4>
                  <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
                    {report.critical_issues.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs: Scores | Transcript | Audit */}
      <Tabs defaultValue="scores">
        <TabsList>
          <TabsTrigger value="scores">Score Breakdown (16 Parameters)</TabsTrigger>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
          <TabsTrigger value="audit">Audit Info</TabsTrigger>
        </TabsList>

        <TabsContent value="scores" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scoreEntries.map(([key, data]) => (
              <ScoreCard key={key} paramKey={key} data={data} />
            ))}
          </div>

          {/* Improvement Suggestions */}
          {report.improvements && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Improvement Suggestions</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                  {report.improvements}
                </pre>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="transcript" className="mt-4">
          {call.transcript ? (
            <TranscriptViewer transcript={call.transcript} />
          ) : (
            <p className="text-gray-400">No transcript available.</p>
          )}
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          <Card>
            <CardContent className="pt-6 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">LLM Model</span>
                <span>{report.llm_model || "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Prompt Version</span>
                <span>{report.prompt_version || "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Rule Engine Version</span>
                <span>{report.rule_engine_version || "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Evaluation Duration</span>
                <span>{report.eval_duration_ms ? `${(report.eval_duration_ms / 1000).toFixed(1)}s` : "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">STT Engine</span>
                <span>{call.stt_engine_used || "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Whisper Confidence</span>
                <span>{call.whisper_confidence != null ? `${(call.whisper_confidence * 100).toFixed(0)}%` : "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Report Generated</span>
                <span>{formatDate(report.created_at)}</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
