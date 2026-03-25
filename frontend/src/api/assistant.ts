const TOKEN_KEY = "erpforge_token";

export interface StreamChunk {
  type: "text" | "tool_use" | "tool_result" | "error" | "done";
  content?: string;
  tool?: string;
  input?: Record<string, unknown>;
  conversation_id?: string;
}

export interface PageContext {
  current_page: string;
  page_data_summary: Record<string, unknown>;
}

export async function sendChatMessage(
  message: string,
  conversationId: string | null,
  pageContext: PageContext,
  onChunk: (chunk: StreamChunk) => void
): Promise<void> {
  const token = localStorage.getItem(TOKEN_KEY);

  const response = await fetch("/api/assistant/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      page_context: pageContext,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Chat request failed" }));
    throw new Error(err.detail || "Chat request failed");
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const chunk = JSON.parse(line.slice(6)) as StreamChunk;
          onChunk(chunk);
        } catch {
          // ignore parse errors
        }
      }
    }
  }
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const token = localStorage.getItem(TOKEN_KEY);
  const response = await fetch("/api/assistant/conversations", {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) return [];
  return response.json();
}
