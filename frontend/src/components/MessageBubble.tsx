"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot } from "lucide-react";
import type { Message } from "@/lib/types";
import { SourceCitation } from "./SourceCitation";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex gap-3 justify-end">
        <div className="max-w-[70%]">
          <div className="bg-nova-600 text-white px-4 py-2.5 rounded-2xl rounded-br-md">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          </div>
        </div>
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-nova-100 flex items-center justify-center">
          <User className="w-4 h-4 text-nova-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
        <Bot className="w-4 h-4 text-gray-600" />
      </div>
      <div className="max-w-[80%] min-w-0">
        <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
          {message.content ? (
            <div
              className={`prose prose-sm max-w-none prose-p:leading-relaxed prose-p:my-1.5 prose-headings:my-2 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-pre:my-2 prose-code:text-xs ${
                message.isStreaming ? "typing-cursor" : ""
              }`}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          ) : message.isStreaming ? (
            <div className="flex items-center gap-1.5 py-1">
              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
            </div>
          ) : null}
          {!message.isStreaming && message.sources && (
            <SourceCitation sources={message.sources} />
          )}
        </div>
      </div>
    </div>
  );
}
