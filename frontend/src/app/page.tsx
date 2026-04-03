"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getAnalyticsSummary, getAgentStats, getParameterStats } from "@/lib/api";
import type { AnalyticsSummary, AgentStats, ParameterStats } from "@/lib/types";
import { gradeColor } from "@/lib/utils";

export default function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [agents, setAgents] = useState<AgentStats[]>([]);
  const [parameters, setParameters] = useState<ParameterStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, a, p] = await Promise.all([
          getAnalyticsSummary(),
          getAgentStats(),
          getParameterStats(),
        ]);
        setSummary(s);
        setAgents(a);
        setParameters(p);
      } catch {
        // API may not be running yet
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="text-gray-500">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of sales call quality metrics</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Total Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{summary?.total_calls || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Evaluated</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-600">{summary?.total_evaluated || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Avg Score</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-emerald-600">{summary?.avg_score || 0}/100</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Quick Action</CardTitle>
          </CardHeader>
          <CardContent>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Upload Call
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Grade Distribution */}
      {summary && Object.keys(summary.grade_distribution).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Grade Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 flex-wrap">
              {Object.entries(summary.grade_distribution)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([grade, count]) => (
                  <div key={grade} className={`px-4 py-2 rounded-lg border ${gradeColor(grade)}`}>
                    <span className="text-lg font-bold">{grade}</span>
                    <span className="text-sm ml-2">({count})</span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Leaderboard */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Leaderboard</CardTitle>
          </CardHeader>
          <CardContent>
            {agents.length === 0 ? (
              <p className="text-gray-400 text-sm">No agent data yet. Upload and evaluate calls to see rankings.</p>
            ) : (
              <div className="space-y-3">
                {agents.slice(0, 10).map((agent, idx) => (
                  <div key={agent.agent_name} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-mono text-gray-400 w-6">#{idx + 1}</span>
                      <span className="font-medium">{agent.agent_name}</span>
                      <span className="text-xs text-gray-400">({agent.total_calls} calls)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{agent.avg_score}</span>
                      <Badge className={gradeColor(agent.avg_grade)}>{agent.avg_grade}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Weakest Parameters */}
        <Card>
          <CardHeader>
            <CardTitle>Parameter Performance (Weakest First)</CardTitle>
          </CardHeader>
          <CardContent>
            {parameters.length === 0 ? (
              <p className="text-gray-400 text-sm">No data yet.</p>
            ) : (
              <div className="space-y-3">
                {parameters.slice(0, 10).map((param) => (
                  <div key={param.parameter} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{param.parameter.replace(/_/g, " ")}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-100 rounded-full h-2">
                        <div
                          className={`h-full rounded-full ${
                            param.avg_percentage >= 70 ? "bg-emerald-500" : param.avg_percentage >= 50 ? "bg-yellow-500" : "bg-red-500"
                          }`}
                          style={{ width: `${param.avg_percentage}%` }}
                        />
                      </div>
                      <span className="text-sm font-mono w-12 text-right">{param.avg_percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
