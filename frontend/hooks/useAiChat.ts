"use client";

import { useState, useCallback } from "react";
import { askAi } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function useAiChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (message: string, context?: string) => {
      setError(null);
      const userMsg: ChatMessage = { role: "user", content: message };
      setMessages((prev) => [...prev, userMsg]);

      // Placeholder assistant message that will be filled by stream
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      setIsStreaming(true);

      try {
        const res = await askAi({ message, context });
        const reader = res.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let done = false;

        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = {
                ...last,
                content: last.content + chunk,
              };
              return updated;
            });
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur inconnue");
        // Remove empty assistant message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsStreaming(false);
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isStreaming, error, sendMessage, reset };
}
