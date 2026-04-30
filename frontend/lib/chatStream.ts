/**
 * Chat SSE consumer — POSTs to /api/chat and streams response events.
 */

import { useStore, type Message } from "./store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatEvent {
  event: "tool_call" | "tool_result" | "token" | "dashboard_action" | "inline_chart" | "done";
  data: Record<string, unknown>;
}

export async function sendChatMessage(
  message: string,
  history: Array<{ role: string; content: string }>,
  context?: string | null,
  onEvent?: (event: ChatEvent) => void,
): Promise<string> {
  const store = useStore.getState();

  // Add user message
  const userMsg: Message = {
    id: crypto.randomUUID(),
    role: "user",
    content: message,
  };
  store.addMessage(userMsg);

  // Create assistant message placeholder
  const assistantMsg: Message = {
    id: crypto.randomUUID(),
    role: "assistant",
    content: "",
    toolBadges: [],
  };
  store.addMessage(assistantMsg);

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, context }),
  });

  if (!response.ok || !response.body) {
    const errorText = "Sorry, I couldn't process that request.";
    updateAssistantMessage(assistantMsg.id, errorText);
    return errorText;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";
  const toolBadges: string[] = [];
  const dashboardActions: Record<string, unknown>[] = [];

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let eventType = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        eventType = line.slice(7).trim();
      } else if (line.startsWith("data: ") && eventType) {
        try {
          const data = JSON.parse(line.slice(6));
          const event: ChatEvent = { event: eventType as ChatEvent["event"], data };

          if (onEvent) onEvent(event);

          switch (eventType) {
            case "tool_call":
              toolBadges.push(data.tool);
              updateAssistantMessage(assistantMsg.id, fullText, [...toolBadges]);
              break;
            case "tool_result":
              // Badge already added on tool_call
              break;
            case "token":
              fullText += data.text || "";
              updateAssistantMessage(assistantMsg.id, fullText, [...toolBadges]);
              break;
            case "dashboard_action":
              dashboardActions.push(data);
              break;
            case "inline_chart":
              updateAssistantMessageChart(assistantMsg.id, data);
              break;
            case "done":
              break;
          }
        } catch {
          // Ignore malformed events
        }
        eventType = "";
      }
    }
  }

  // Apply dashboard actions after stream completes — switch tab once, then apply all
  if (dashboardActions.length > 0) {
    const targetTab = dashboardActions.find((a) => a.target_tab && a.target_tab !== "none")?.target_tab as string | undefined;
    if (targetTab) {
      const store = useStore.getState();
      if (targetTab !== store.activeTab) {
        store.setActiveTab(targetTab as "live_store" | "analytics" | "executive");
      }
      if (targetTab === "live_store" && !store.demoMode) {
        store.setDemoMode(true);
      }
    }
    for (const action of dashboardActions) {
      applyDashboardAction(action);
    }
  }

  return fullText;
}

function updateAssistantMessage(id: string, content: string, toolBadges?: string[]) {
  const store = useStore.getState();
  const messages = store.chatMessages.map((m) =>
    m.id === id ? { ...m, content, toolBadges: toolBadges || m.toolBadges } : m,
  );
  // Directly set messages via internal state update
  useStore.setState({ chatMessages: messages });
}

function updateAssistantMessageChart(id: string, chartData: Record<string, unknown>) {
  const store = useStore.getState();
  const messages = store.chatMessages.map((m) =>
    m.id === id ? { ...m, inlineChart: chartData } : m,
  );
  useStore.setState({ chatMessages: messages });
}

function applyDashboardAction(data: Record<string, unknown>) {
  const store = useStore.getState();

  switch (data.type) {
    case "highlight_fixture":
      if (data.id) {
        store.setHighlightedFixtures([...(store.highlightedFixtures || []), data.id as string]);
        setTimeout(() => {
          const current = useStore.getState().highlightedFixtures;
          store.setHighlightedFixtures(current.filter((f) => f !== data.id));
        }, 8000);
      }
      break;
    case "filter_category":
    case "filter_sku":
      if (data.id) {
        store.setGridFilter(
          data.type === "filter_category"
            ? { category: data.id as string }
            : { sku: data.id as string },
        );
      }
      break;
  }
}
