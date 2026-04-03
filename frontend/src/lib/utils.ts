import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function gradeColor(grade: string): string {
  switch (grade) {
    case "A+": return "text-emerald-600 bg-emerald-50 border-emerald-200";
    case "A": return "text-green-600 bg-green-50 border-green-200";
    case "B+": return "text-blue-600 bg-blue-50 border-blue-200";
    case "B": return "text-sky-600 bg-sky-50 border-sky-200";
    case "C": return "text-yellow-600 bg-yellow-50 border-yellow-200";
    case "D": return "text-orange-600 bg-orange-50 border-orange-200";
    case "F": return "text-red-600 bg-red-50 border-red-200";
    default: return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

export function scoreColor(score: number, max: number): string {
  const pct = max > 0 ? (score / max) * 100 : 0;
  if (pct >= 80) return "text-emerald-600";
  if (pct >= 60) return "text-blue-600";
  if (pct >= 40) return "text-yellow-600";
  return "text-red-600";
}

export function scoreBarColor(score: number, max: number): string {
  const pct = max > 0 ? (score / max) * 100 : 0;
  if (pct >= 80) return "bg-emerald-500";
  if (pct >= 60) return "bg-blue-500";
  if (pct >= 40) return "bg-yellow-500";
  return "bg-red-500";
}

export function formatDuration(seconds: number | null): string {
  if (!seconds) return "--:--";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    UPLOADED: "Uploaded",
    PREPROCESSING: "Preprocessing",
    TRANSCRIBING: "Transcribing",
    EVALUATING: "Evaluating",
    COMPLETED: "Completed",
    FAILED: "Failed",
  };
  return map[status] || status;
}

export function statusColor(status: string): string {
  switch (status) {
    case "COMPLETED": return "bg-emerald-100 text-emerald-700";
    case "FAILED": return "bg-red-100 text-red-700";
    case "UPLOADED": return "bg-gray-100 text-gray-700";
    default: return "bg-blue-100 text-blue-700";
  }
}
