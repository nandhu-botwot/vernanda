"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listCalls } from "@/lib/api";
import type { CallListItem } from "@/lib/types";
import { formatDate, formatDuration, statusColor, statusLabel, gradeColor } from "@/lib/utils";

export default function CallsPage() {
  const [calls, setCalls] = useState<CallListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await listCalls({ page, limit: 20 });
        setCalls(data.calls);
        setTotal(data.total);
      } catch {
        // API may not be running
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [page]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
          <p className="text-gray-500 mt-1">{total} total calls</p>
        </div>
        <Link
          href="/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Upload New Call
        </Link>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <p className="p-6 text-gray-400">Loading...</p>
          ) : calls.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-400">No calls uploaded yet.</p>
              <Link href="/upload" className="text-blue-600 hover:underline text-sm mt-2 inline-block">
                Upload your first call
              </Link>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">File</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Agent</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Duration</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Score</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Grade</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {calls.map((call) => (
                  <tr key={call.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link href={call.status === "COMPLETED" ? `/reports/${call.id}` : `/calls/${call.id}`} className="text-blue-600 hover:underline">
                        {call.filename}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-700">{call.agent_name || "-"}</td>
                    <td className="px-4 py-3 text-gray-500">{formatDuration(call.duration_seconds)}</td>
                    <td className="px-4 py-3">
                      <Badge className={statusColor(call.status)}>{statusLabel(call.status)}</Badge>
                    </td>
                    <td className="px-4 py-3 font-bold">
                      {call.total_score != null ? `${call.total_score}/100` : "-"}
                    </td>
                    <td className="px-4 py-3">
                      {call.grade ? (
                        <Badge className={gradeColor(call.grade)}>{call.grade}</Badge>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(call.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 rounded border text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-sm text-gray-500">
            Page {page} of {Math.ceil(total / 20)}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * 20 >= total}
            className="px-3 py-1 rounded border text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
