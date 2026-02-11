"use client";

import type { Conversation } from "@/lib/types";
import { MessageSquarePlus, MessagesSquare } from "lucide-react";

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
}

export function Sidebar({
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
}: SidebarProps) {
  return (
    <aside className="flex flex-col w-72 bg-sidebar text-white border-r border-gray-800 flex-shrink-0">
      {/* Logo area */}
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-800/50">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-nova-600 text-white font-bold text-sm">
          N
        </div>
        <div>
          <div className="font-semibold text-sm">NovaPay</div>
          <div className="text-xs text-gray-400">Docs Portal</div>
        </div>
      </div>

      {/* New chat button */}
      <div className="px-3 py-3">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-sidebar-hover rounded-lg transition-colors"
        >
          <MessageSquarePlus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-3">
        {conversations.length > 0 && (
          <div className="mb-2">
            <div className="px-3 py-1.5 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Recent Queries
            </div>
            <div className="space-y-0.5">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg transition-colors text-left ${
                    conv.id === activeConversationId
                      ? "bg-sidebar-active text-white"
                      : "text-gray-400 hover:text-gray-200 hover:bg-sidebar-hover"
                  }`}
                >
                  <MessagesSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                  <span className="truncate">{conv.title}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-gray-800/50">
        <div className="text-xs text-gray-500">
          NovaPay Docs Portal v1.0
        </div>
      </div>
    </aside>
  );
}
