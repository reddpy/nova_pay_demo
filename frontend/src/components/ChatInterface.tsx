"use client";

import { useState, useRef, useEffect, useCallback, KeyboardEvent } from "react";
import { Send, Square, Sparkles } from "lucide-react";
import type { Message } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

interface ChatInterfaceProps {
  messages: Message[];
  isStreaming: boolean;
  onSendMessage: (question: string) => void;
  onStopStreaming: () => void;
  onSampleQuery: (query: string) => void;
  showWelcome: boolean;
}

const SAMPLE_QUERIES = [
  "How do I set up my local dev environment?",
  "What's the rate limit on the payments API?",
  "What should I do if payments service is down?",
  "How does our auth system work?",
  "What do I need to do before deploying?",
];

export function ChatInterface({
  messages,
  isStreaming,
  onSendMessage,
  onStopStreaming,
  onSampleQuery,
  showWelcome,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = Math.min(textarea.scrollHeight, 150) + "px";
    }
  }, [input]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    onSendMessage(trimmed);
    setInput("");
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, isStreaming, onSendMessage]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {showWelcome && messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-4">
            <div className="max-w-lg text-center">
              <div className="flex items-center justify-center w-14 h-14 mx-auto mb-4 rounded-2xl bg-nova-50 border border-nova-100">
                <Sparkles className="w-7 h-7 text-nova-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Ask about NovaPay engineering docs
              </h2>
              <p className="text-sm text-gray-500 mb-8">
                I can help you find information about our APIs, architecture,
                processes, and runbooks. Try one of these questions:
              </p>
              <div className="space-y-2">
                {SAMPLE_QUERIES.map((query) => (
                  <button
                    key={query}
                    onClick={() => onSampleQuery(query)}
                    className="block w-full px-4 py-2.5 text-sm text-left text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-colors"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus-within:border-nova-300 focus-within:ring-1 focus-within:ring-nova-300 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about NovaPay engineering docs..."
              rows={1}
              className="flex-1 bg-transparent text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none py-1 max-h-36"
              disabled={isStreaming}
            />
            {isStreaming ? (
              <button
                onClick={onStopStreaming}
                className="flex-shrink-0 p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                title="Stop generating"
              >
                <Square className="w-4 h-4 fill-current" />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="flex-shrink-0 p-1.5 text-nova-600 hover:bg-nova-50 rounded-lg transition-colors disabled:text-gray-300 disabled:hover:bg-transparent"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-1.5 text-center">
            Answers are generated from NovaPay internal docs. Always verify critical information.
          </p>
        </div>
      </div>
    </div>
  );
}
