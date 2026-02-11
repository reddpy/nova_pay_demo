"use client";

import { useState, useCallback } from "react";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { ChatInterface } from "@/components/ChatInterface";
import type { Conversation, Message, Source } from "@/lib/types";
import { streamChat } from "@/lib/api";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [abortController, setAbortController] =
    useState<AbortController | null>(null);

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId
  );

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null);
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    setActiveConversationId(id);
  }, []);

  const handleSendMessage = useCallback(
    async (question: string) => {
      if (isStreaming) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
      };

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      let convId = activeConversationId;

      if (!convId) {
        // Create new conversation
        convId = crypto.randomUUID();
        const newConv: Conversation = {
          id: convId,
          title: question.slice(0, 60) + (question.length > 60 ? "..." : ""),
          messages: [userMessage, assistantMessage],
        };
        setConversations((prev) => [newConv, ...prev]);
        setActiveConversationId(convId);
      } else {
        // Add to existing conversation
        setConversations((prev) =>
          prev.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  messages: [...c.messages, userMessage, assistantMessage],
                }
              : c
          )
        );
      }

      const controller = new AbortController();
      setAbortController(controller);
      setIsStreaming(true);

      const currentConvId = convId;

      try {
        await streamChat(
          question,
          (token: string) => {
            setConversations((prev) =>
              prev.map((c) => {
                if (c.id !== currentConvId) return c;
                const messages = [...c.messages];
                const lastMsg = messages[messages.length - 1];
                if (lastMsg.role === "assistant") {
                  messages[messages.length - 1] = {
                    ...lastMsg,
                    content: lastMsg.content + token,
                  };
                }
                return { ...c, messages };
              })
            );
          },
          (sources: Source[]) => {
            setConversations((prev) =>
              prev.map((c) => {
                if (c.id !== currentConvId) return c;
                const messages = [...c.messages];
                const lastMsg = messages[messages.length - 1];
                if (lastMsg.role === "assistant") {
                  messages[messages.length - 1] = {
                    ...lastMsg,
                    sources,
                  };
                }
                return { ...c, messages };
              })
            );
          },
          () => {
            setConversations((prev) =>
              prev.map((c) => {
                if (c.id !== currentConvId) return c;
                const messages = [...c.messages];
                const lastMsg = messages[messages.length - 1];
                if (lastMsg.role === "assistant") {
                  messages[messages.length - 1] = {
                    ...lastMsg,
                    isStreaming: false,
                  };
                }
                return { ...c, messages };
              })
            );
            setIsStreaming(false);
            setAbortController(null);
          },
          (error: Error) => {
            console.error("Stream error:", error);
            setConversations((prev) =>
              prev.map((c) => {
                if (c.id !== currentConvId) return c;
                const messages = [...c.messages];
                const lastMsg = messages[messages.length - 1];
                if (lastMsg.role === "assistant") {
                  messages[messages.length - 1] = {
                    ...lastMsg,
                    content:
                      lastMsg.content ||
                      "Sorry, an error occurred. Please make sure the backend is running and try again.",
                    isStreaming: false,
                  };
                }
                return { ...c, messages };
              })
            );
            setIsStreaming(false);
            setAbortController(null);
          },
          controller.signal
        );
      } catch {
        // AbortError is expected when user cancels
        setIsStreaming(false);
        setAbortController(null);
      }
    },
    [activeConversationId, isStreaming]
  );

  const handleStopStreaming = useCallback(() => {
    abortController?.abort();
    setIsStreaming(false);
    setAbortController(null);

    // Mark the last assistant message as not streaming
    if (activeConversationId) {
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== activeConversationId) return c;
          const messages = [...c.messages];
          const lastMsg = messages[messages.length - 1];
          if (lastMsg.role === "assistant") {
            messages[messages.length - 1] = {
              ...lastMsg,
              isStreaming: false,
            };
          }
          return { ...c, messages };
        })
      );
    }
  }, [abortController, activeConversationId]);

  const handleSampleQuery = useCallback(
    (query: string) => {
      handleSendMessage(query);
    },
    [handleSendMessage]
  );

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
      />
      <div className="flex flex-col flex-1 min-w-0">
        <Header />
        <ChatInterface
          messages={activeConversation?.messages || []}
          isStreaming={isStreaming}
          onSendMessage={handleSendMessage}
          onStopStreaming={handleStopStreaming}
          onSampleQuery={handleSampleQuery}
          showWelcome={!activeConversationId}
        />
      </div>
    </div>
  );
}
