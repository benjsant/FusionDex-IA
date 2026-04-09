"use client";

import { useState, useRef, useEffect } from "react";
import { useAiChat } from "@/hooks/useAiChat";
import type { ChatMessage } from "@/hooks/useAiChat";

const SUGGESTIONS = [
  "Meilleure fusion Dracaufeu ?",
  "Quelle équipe pour un run Nuzlocke ?",
  "Comment obtenir les Pokémon légendaires dans IF ?",
  "Quels sont les types les plus forts dans Infinite Fusion ?",
];

export function AiChat({ initialMessage }: { initialMessage?: string }) {
  const { messages, isStreaming, error, sendMessage, reset } = useAiChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  // Auto-send initial message
  useEffect(() => {
    if (initialMessage) {
      sendMessage(initialMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 gap-6">
            <div className="text-4xl">🤖</div>
            <p className="text-[rgb(160,160,180)] text-sm text-center max-w-xs">
              Pose-moi une question sur Pokémon Infinite Fusion, les stratégies de fusion, les équipes…
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-xs px-3 py-1.5 rounded-full bg-[rgb(25,25,38)] border border-[rgb(50,50,70)] text-[rgb(160,160,200)] hover:border-indigo-500 hover:text-indigo-300 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isStreaming && messages[messages.length - 1]?.content === "" && (
          <div className="flex gap-1 items-center pl-10">
            <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
        )}

        {error && (
          <p className="text-red-400 text-sm text-center py-2">{error}</p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[rgb(40,40,55)] pt-4 mt-4">
        {messages.length > 0 && (
          <button
            onClick={reset}
            className="text-xs text-[rgb(100,100,120)] hover:text-[rgb(160,160,180)] mb-2 transition-colors"
          >
            Effacer la conversation
          </button>
        )}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming}
            placeholder="Pose ta question…"
            className="flex-1 px-4 py-2 rounded-lg bg-[rgb(25,25,38)] border border-[rgb(50,50,70)] text-[rgb(220,220,255)] placeholder:text-[rgb(80,80,100)] focus:outline-none focus:border-indigo-500 disabled:opacity-50 transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {isStreaming ? "…" : "Envoyer"}
          </button>
        </form>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-indigo-700 flex items-center justify-center text-xs shrink-0 mr-2 mt-0.5">
          🤖
        </div>
      )}
      <div
        className={`max-w-[80%] px-4 py-2.5 rounded-xl text-sm whitespace-pre-wrap leading-relaxed ${
          isUser
            ? "bg-indigo-600/30 text-[rgb(220,220,255)] rounded-br-sm"
            : "bg-[rgb(25,25,38)] text-[rgb(200,200,220)] rounded-bl-sm"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
