"use client";

import type { Message } from "@/lib/store";
import ReactMarkdown from "react-markdown";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
          isUser
            ? "bg-[var(--accent-cyan)] text-[var(--bg-deep)]"
            : "bg-[var(--card-bg)] text-[var(--text-primary)] border border-[var(--border)]"
        }`}
      >
        {/* Tool badges */}
        {message.toolBadges && message.toolBadges.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-1.5">
            {message.toolBadges.map((tool, i) => (
              <span
                key={i}
                className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-[var(--bg-deep)] text-[var(--accent-mint)] border border-[var(--border)]"
              >
                {tool}
              </span>
            ))}
          </div>
        )}

        {/* Message content */}
        {isUser ? (
          <div className="whitespace-pre-wrap">{message.content || "..."}</div>
        ) : (
          <div className="prose-chat">
            <ReactMarkdown>{message.content || "..."}</ReactMarkdown>
          </div>
        )}

        {/* Inline chart placeholder */}
        {message.inlineChart && (
          <div className="mt-2 p-2 rounded bg-[var(--bg-deep)] border border-[var(--border)] text-[10px] text-[var(--text-muted)]">
            [Chart: {(message.inlineChart as Record<string, unknown>).type || "data"}]
          </div>
        )}
      </div>
    </div>
  );
}
