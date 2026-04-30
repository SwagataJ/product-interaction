"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X, Send } from "lucide-react";
import { useStore } from "@/lib/store";
import { sendChatMessage } from "@/lib/chatStream";
import MessageBubble from "./MessageBubble";

export default function ChatPanel() {
  const { chatOpen, setChatOpen, chatMessages, chatPendingContext, setChatPendingContext } = useStore();
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Handle pending context (click-driven chat)
  useEffect(() => {
    if (chatPendingContext && chatOpen && !isLoading) {
      handleSend(chatPendingContext);
      setChatPendingContext(null);
    }
  }, [chatPendingContext, chatOpen]);

  const handleSend = async (text?: string) => {
    const message = text || input.trim();
    if (!message || isLoading) return;

    setInput("");
    setIsLoading(true);

    const history = chatMessages
      .filter((m) => m.content)
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      await sendChatMessage(message, history);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Collapsed pill */}
      <AnimatePresence>
        {!chatOpen && (
          <motion.button
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            onClick={() => setChatOpen(true)}
            className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-full bg-[var(--accent-cyan)] text-[var(--bg-deep)] font-medium text-sm shadow-lg hover:scale-105 transition-transform"
          >
            <MessageCircle size={16} />
            Ask AI
          </motion.button>
        )}
      </AnimatePresence>

      {/* Expanded panel */}
      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed bottom-6 right-6 z-50 w-[380px] h-[520px] flex flex-col rounded-xl border border-[var(--border)] bg-[var(--bg-deep)] shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[var(--accent-mint)] animate-pulse" />
                <span className="text-sm font-medium text-[var(--text-primary)]">Store Analyst</span>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="p-1 rounded hover:bg-[var(--card-bg)] text-[var(--text-muted)]"
              >
                <X size={16} />
              </button>
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {chatMessages.length === 0 && (
                <div className="text-center text-[var(--text-muted)] text-xs mt-8">
                  <p className="mb-2">Ask about your store performance</p>
                  <div className="space-y-1.5">
                    {[
                      "How much revenue did we lose to stockouts?",
                      "Why did Men's Shirts under-perform?",
                      "Where is shrinkage concentrated?",
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => handleSend(q)}
                        className="block w-full text-left px-3 py-1.5 rounded border border-[var(--border)] hover:border-[var(--accent-cyan)] hover:text-[var(--text-primary)] text-xs transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {chatMessages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div className="flex gap-1 px-3 py-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-cyan)] animate-bounce" />
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-cyan)] animate-bounce [animation-delay:0.1s]" />
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-cyan)] animate-bounce [animation-delay:0.2s]" />
                </div>
              )}
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-[var(--border)]">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about your store..."
                  className="flex-1 bg-[var(--card-bg)] text-[var(--text-primary)] text-sm px-3 py-2 rounded-lg border border-[var(--border)] focus:outline-none focus:border-[var(--accent-cyan)] placeholder:text-[var(--text-muted)]"
                  disabled={isLoading}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || isLoading}
                  className="p-2 rounded-lg bg-[var(--accent-cyan)] text-[var(--bg-deep)] disabled:opacity-40 hover:opacity-90 transition-opacity"
                >
                  <Send size={14} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
