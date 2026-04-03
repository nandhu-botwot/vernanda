"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getAnalyticsSummary, getAgentStats, getParameterStats } from "@/lib/api";
import type { AnalyticsSummary, AgentStats, ParameterStats } from "@/lib/types";
import { gradeColor } from "@/lib/utils";

export default function AnalyticsPage() {
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
        // API may not be running
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <p className="text-gray-400">Loading analytics...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-500 mt-1">Detailed performance analysis across agents and parameters</p>
      </div>

      {/* Agent Leaderboard - Full Table */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Performance</CardTitle>
        </CardHeader>
        <CardContent>
          {agents.length === 0 ? (
            <p className="text-gray-400 text-sm">No data yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Rank</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Agent</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Calls</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Avg Score</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Best</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Worst</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Grade</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {agents.map((agent, idx) => (
                  <tr key={agent.agent_name} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-gray-400">#{idx + 1}</td>
                    <td className="px-4 py-3 font-medium">{agent.agent_name}</td>
                    <td className="px-4 py-3">{agent.total_calls}</td>
                    <td className="px-4 py-3 font-bold">{agent.avg_score}</td>
                    <td className="px-4 py-3 text-emerald-600">{agent.best_score}</td>
                    <td className="px-4 py-3 text-red-600">{agent.worst_score}</td>
                    <td className="px-4 py-3">
                      <Badge className={gradeColor(agent.avg_grade)}>{agent.avg_grade}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* Parameter Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle>Parameter Performance (Team Average)</CardTitle>
        </CardHeader>
        <CardContent>
          {parameters.length === 0 ? (
            <p className="text-gray-400 text-sm">No data yet.</p>
          ) : (
            <div className="space-y-3">
              {parameters.map((param) => (
                <div key={param.parameter} className="flex items-center gap-4">
                  <span className="text-sm w-48 capitalize truncate">{param.parameter.replace(/_/g, " ")}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        param.avg_percentage >= 70
                          ? "bg-emerald-500"
                          : param.avg_percentage >= 50
                          ? "bg-yellow-500"
                          : "bg-red-500"
                      }`}
                      style={{ width: `${param.avg_percentage}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono w-16 text-right">
                    {param.avg_score}/{param.max_possible}
                  </span>
                  <span className="text-sm font-mono w-12 text-right text-gray-500">
                    {param.avg_percentage}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
