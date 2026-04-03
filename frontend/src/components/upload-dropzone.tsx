"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { uploadCall } from "@/lib/api";

const ACCEPTED_TYPES = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac", ".aac"];

export default function UploadDropzone() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [agentName, setAgentName] = useState("");
  const [callLanguage, setCallLanguage] = useState("en");
  const [callType, setCallType] = useState("");
  const [previousFeedback, setPreviousFeedback] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      validateAndSetFile(dropped);
    }
  }, []);

  const validateAndSetFile = (f: File) => {
    setError("");
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      setError(`Unsupported format: ${ext}. Allowed: ${ACCEPTED_TYPES.join(", ")}`);
      return;
    }
    if (f.size > 200 * 1024 * 1024) {
      setError("File too large. Maximum: 200MB");
      return;
    }
    setFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (agentName) formData.append("agent_name", agentName);
      formData.append("call_language", callLanguage);
      if (callType) formData.append("call_type", callType);
      if (previousFeedback) formData.append("previous_feedback", previousFeedback);

      const result = await uploadCall(formData);
      router.push(`/calls/${result.call_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload Sales Call Recording</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            className={`border-2 border-dashed rounded-lg p-10 text-center transition-colors ${
              dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
            }`}
          >
            {file ? (
              <div>
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500 mt-1">
                  {(file.size / (1024 * 1024)).toFixed(1)} MB
                </p>
                <button
                  onClick={() => setFile(null)}
                  className="text-sm text-red-500 hover:underline mt-2"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div>
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="mt-2 text-sm text-gray-600">
                  Drag & drop audio file, or{" "}
                  <label className="text-blue-600 hover:underline cursor-pointer">
                    browse
                    <input
                      type="file"
                      className="hidden"
                      accept={ACCEPTED_TYPES.join(",")}
                      onChange={(e) => e.target.files?.[0] && validateAndSetFile(e.target.files[0])}
                    />
                  </label>
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  MP3, WAV, M4A, OGG, FLAC, AAC (max 200MB)
                </p>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Agent Name</label>
              <input
                type="text"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="e.g. Priya"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
              <select
                value={callLanguage}
                onChange={(e) => setCallLanguage(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="en">English</option>
                <option value="ta">Tamil</option>
                <option value="hi">Hindi</option>
                <option value="ml">Malayalam</option>
                <option value="kn">Kannada</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Call Type</label>
              <select
                value={callType}
                onChange={(e) => setCallType(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select...</option>
                <option value="INBOUND">Inbound</option>
                <option value="OUTBOUND">Outbound</option>
              </select>
            </div>
          </div>

          {/* Previous feedback (for Repeated Mistakes param) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Previous QA Feedback (optional)
            </label>
            <textarea
              value={previousFeedback}
              onChange={(e) => setPreviousFeedback(e.target.value)}
              placeholder="Paste feedback from the agent's last QA review..."
              rows={3}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400 mt-1">
              Used to check for repeated mistakes. Leave blank if this is the first evaluation.
            </p>
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-md p-3">{error}</p>
          )}

          <Button
            onClick={handleSubmit}
            disabled={!file || uploading}
            className="w-full"
            size="lg"
          >
            {uploading ? "Uploading..." : "Upload & Analyze"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
