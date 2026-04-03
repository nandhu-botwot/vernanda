"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { scoreColor, scoreBarColor } from "@/lib/utils";
import type { ParameterScore } from "@/lib/types";

interface ScoreCardProps {
  paramKey: string;
  data: ParameterScore;
}

export default function ScoreCard({ paramKey, data }: ScoreCardProps) {
  const [expanded, setExpanded] = useState(false);
  const pct = data.max_score > 0 ? (data.score / data.max_score) * 100 : 0;
  const label = data.label || paramKey.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => setExpanded(!expanded)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{label}</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {data.method}
            </Badge>
            <span className={`text-lg font-bold ${scoreColor(data.score, data.max_score)}`}>
              {data.score}/{data.max_score}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${scoreBarColor(data.score, data.max_score)}`}
            style={{ width: `${pct}%` }}
          />
        </div>

        {expanded && (
          <div className="mt-4 space-y-3 text-sm">
            {data.feedback && (
              <div>
                <p className="font-medium text-gray-700">Feedback</p>
                <p className="text-gray-600">{data.feedback}</p>
              </div>
            )}
            {data.evidence.length > 0 && (
              <div>
                <p className="font-medium text-gray-700">Evidence</p>
                <ul className="list-disc list-inside text-gray-600 space-y-1">
                  {data.evidence.map((e, i) => (
                    <li key={i} className="text-xs italic">
                      &quot;{e}&quot;
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.improvement && (
              <div>
                <p className="font-medium text-gray-700">Improvement</p>
                <p className="text-blue-600">{data.improvement}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
