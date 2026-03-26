import { CloseOutlined, PlusOutlined, QuestionCircleOutlined, SendOutlined } from "@ant-design/icons";
import { Button, Drawer, Input, Typography } from "antd";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useCopilot } from "../hooks/useCopilot";
import CopilotMessage, { StreamingIndicator } from "./CopilotMessage";

const { Text } = Typography;

interface CopilotWidgetProps {
  initialPrompt?: string | null;
  onPromptConsumed?: () => void;
}

export default function CopilotWidget({ initialPrompt, onPromptConsumed }: CopilotWidgetProps) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, streaming, sendMessage, newConversation } = useCopilot();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle initial prompt from onboarding checklist
  useEffect(() => {
    if (initialPrompt && !open) {
      setOpen(true);
    }
  }, [initialPrompt]);

  useEffect(() => {
    if (initialPrompt && open && !streaming) {
      const prompt = initialPrompt;
      onPromptConsumed?.();
      handleSend(prompt);
    }
  }, [initialPrompt, open]);

  const handleSend = useCallback(
    async (text?: string) => {
      const msg = text || input.trim();
      if (!msg || streaming) return;
      setInput("");
      await sendMessage(msg, {
        current_page: location.pathname,
        page_data_summary: {},
      });
    },
    [input, streaming, sendMessage, location.pathname]
  );

  const handleNavigate = useCallback(
    (path: string) => {
      navigate(path);
    },
    [navigate]
  );

  return (
    <>
      {/* Floating button */}
      {!open && (
        <Button
          type="primary"
          shape="circle"
          size="large"
          icon={<QuestionCircleOutlined />}
          onClick={() => setOpen(true)}
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            width: 56,
            height: 56,
            fontSize: 24,
            zIndex: 1000,
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          }}
        />
      )}

      {/* Chat drawer */}
      <Drawer
        title={
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <QuestionCircleOutlined style={{ color: "#52c41a" }} />
              <span>ERPForge Assistant</span>
            </div>
            <Button
              type="text"
              size="small"
              icon={<PlusOutlined />}
              onClick={newConversation}
              title="New conversation"
            >
              New
            </Button>
          </div>
        }
        placement="right"
        width={420}
        open={open}
        onClose={() => setOpen(false)}
        closeIcon={<CloseOutlined />}
        styles={{
          body: {
            padding: 0,
            display: "flex",
            flexDirection: "column",
            height: "100%",
          },
        }}
      >
        {/* Messages area */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "12px 0",
          }}
        >
          {messages.length === 0 && (
            <div style={{ textAlign: "center", padding: "40px 24px" }}>
              <QuestionCircleOutlined style={{ fontSize: 32, color: "#d9d9d9", display: "block", marginBottom: 12 }} />
              <Text type="secondary">
                Ask me anything about ERPForge. I can explain concepts, guide you through workflows,
                and help you create data.
              </Text>
            </div>
          )}
          {messages.map((msg) => (
            <CopilotMessage key={msg.id} message={msg} onNavigate={handleNavigate} />
          ))}
          {streaming && <StreamingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div
          style={{
            borderTop: "1px solid #f0f0f0",
            padding: "12px 16px",
            display: "flex",
            gap: 8,
          }}
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={() => handleSend()}
            placeholder="Ask a question or request an action..."
            disabled={streaming}
            autoFocus
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => handleSend()}
            disabled={!input.trim() || streaming}
          />
        </div>
      </Drawer>
    </>
  );
}
