import { useCallback, useRef, useState } from "react";
import { PageContext, sendChatMessage, StreamChunk } from "../api/assistant";
import { ChatMessage } from "../components/CopilotMessage";

let msgCounter = 0;
function nextId() {
  return `msg-${++msgCounter}-${Date.now()}`;
}

export function useCopilot() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const assistantBufferRef = useRef("");

  const sendMessage = useCallback(
    async (text: string, pageContext: PageContext) => {
      // Add user message
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", content: text },
      ]);

      setStreaming(true);
      assistantBufferRef.current = "";

      // Add placeholder assistant message
      const assistantMsgId = nextId();
      setMessages((prev) => [
        ...prev,
        { id: assistantMsgId, role: "assistant", content: "" },
      ]);

      try {
        await sendChatMessage(text, conversationId, pageContext, (chunk: StreamChunk) => {
          switch (chunk.type) {
            case "text":
              assistantBufferRef.current += chunk.content || "";
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: assistantBufferRef.current }
                    : m
                )
              );
              break;

            case "tool_use":
              setMessages((prev) => [
                ...prev,
                {
                  id: nextId(),
                  role: "tool_use",
                  content: `Using ${chunk.tool}...`,
                  toolName: chunk.tool,
                  toolInput: chunk.input,
                },
              ]);
              break;

            case "tool_result": {
              const content = chunk.content || "";
              // Check if this is a navigation result
              if (content.startsWith("NAVIGATE:")) {
                const parts = content.slice(9).split("|");
                setMessages((prev) => [
                  ...prev,
                  {
                    id: nextId(),
                    role: "tool_result",
                    content: "",
                    navigatePath: parts[0],
                    navigateReason: parts[1] || "",
                  },
                ]);
              } else {
                setMessages((prev) => [
                  ...prev,
                  { id: nextId(), role: "tool_result", content },
                ]);
              }
              // After tool result, Claude will continue streaming text in a new block.
              // Create a new assistant message placeholder for the continuation.
              assistantBufferRef.current = "";
              const newId = nextId();
              setMessages((prev) => [
                ...prev,
                { id: newId, role: "assistant", content: "" },
              ]);
              // Update the assistantMsgId reference for subsequent text chunks
              // We can't reassign assistantMsgId directly, so we use a workaround:
              // The streaming text callback will update the LAST assistant message
              break;
            }

            case "error":
              setMessages((prev) => [
                ...prev,
                { id: nextId(), role: "error", content: chunk.content || "Unknown error" },
              ]);
              break;

            case "done":
              if (chunk.conversation_id) {
                setConversationId(chunk.conversation_id);
              }
              break;
          }
        });
      } catch (e: any) {
        setMessages((prev) => [
          ...prev,
          { id: nextId(), role: "error", content: e.message || "Failed to send message" },
        ]);
      } finally {
        setStreaming(false);
        // Clean up empty assistant messages
        setMessages((prev) => prev.filter((m) => m.role !== "assistant" || m.content.trim() !== ""));
      }
    },
    [conversationId]
  );

  const newConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return {
    messages,
    streaming,
    conversationId,
    sendMessage,
    newConversation,
    setMessages,
  };
}
