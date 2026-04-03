"use client";

interface TranscriptViewerProps {
  transcript: string;
}

export default function TranscriptViewer({ transcript }: TranscriptViewerProps) {
  const lines = transcript.split("\n").filter(Boolean);

  return (
    <div className="bg-gray-50 rounded-lg p-4 max-h-[600px] overflow-y-auto space-y-2 font-mono text-sm">
      {lines.map((line, i) => {
        const isAgent = line.includes("Agent:");
        const isCustomer = line.includes("Customer:");

        // Parse timestamp and content
        const match = line.match(/^\[(\d{2}:\d{2})\]\s*(Agent|Customer):\s*(.*)/);
        if (!match) {
          return (
            <p key={i} className="text-gray-500">
              {line}
            </p>
          );
        }

        const [, timestamp, speaker, text] = match;

        return (
          <div key={i} className={`flex gap-3 ${isAgent ? "pl-0" : "pl-8"}`}>
            <span className="text-gray-400 text-xs mt-1 flex-shrink-0 w-12">
              {timestamp}
            </span>
            <div
              className={`rounded-lg px-3 py-2 max-w-[80%] ${
                isAgent
                  ? "bg-blue-100 text-blue-900"
                  : "bg-green-100 text-green-900"
              }`}
            >
              <span className="font-semibold text-xs block mb-0.5">
                {speaker}
              </span>
              <span>{text}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
