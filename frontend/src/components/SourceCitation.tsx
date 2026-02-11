"use client";

import { useState } from "react";
import { FileText } from "lucide-react";
import type { Source } from "@/lib/types";

interface SourceCitationProps {
  sources: Source[];
}

export function SourceCitation({ sources }: SourceCitationProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <div className="text-xs font-medium text-gray-500 mb-2">Sources</div>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((source, index) => (
          <div key={index} className="relative">
            <button
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-md transition-colors"
            >
              <FileText className="w-3 h-3 text-gray-400" />
              {source.file.split("/").pop()}
            </button>
            {hoveredIndex === index && (
              <div className="absolute bottom-full left-0 mb-2 w-80 p-3 bg-gray-900 text-gray-100 text-xs rounded-lg shadow-xl z-50">
                <div className="font-medium text-nova-300 mb-1">
                  {source.file}
                </div>
                <div className="text-gray-300 leading-relaxed">
                  {source.snippet}
                </div>
                <div className="absolute bottom-0 left-4 w-2 h-2 bg-gray-900 transform rotate-45 translate-y-1" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
