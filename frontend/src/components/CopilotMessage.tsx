import { LinkOutlined, LoadingOutlined, QuestionCircleOutlined, UserOutlined } from "@ant-design/icons";
import { Button, Typography } from "antd";
import React from "react";

const { Text, Paragraph } = Typography;

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "tool_result" | "error";
  content: string;
  navigatePath?: string;
  navigateReason?: string;
}

interface CopilotMessageProps {
  message: ChatMessage;
  onNavigate?: (path: string) => void;
}

export default function CopilotMessage({ message, onNavigate }: CopilotMessageProps) {
  const isUser = message.role === "user";
  const isError = message.role === "error";

  if (message.navigatePath) {
    return (
      <div style={{ padding: "4px 12px" }}>
        <Button
          type="link"
          icon={<LinkOutlined />}
          size="small"
          onClick={() => onNavigate?.(message.navigatePath!)}
        >
          Go to {message.navigatePath}
        </Button>
        {message.navigateReason && (
          <Text type="secondary" style={{ fontSize: 12, display: "block" }}>
            {message.navigateReason}
          </Text>
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        gap: 8,
        padding: "8px 12px",
        background: isUser ? "#f6f8fa" : isError ? "#fff2f0" : "transparent",
        borderRadius: 8,
      }}
    >
      <div style={{ flexShrink: 0, paddingTop: 2 }}>
        {isUser ? (
          <UserOutlined style={{ color: "#1677ff" }} />
        ) : (
          <QuestionCircleOutlined style={{ color: isError ? "#ff4d4f" : "#52c41a" }} />
        )}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Paragraph
          style={{
            margin: 0,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontSize: 13,
            color: isError ? "#ff4d4f" : undefined,
          }}
        >
          {message.content}
        </Paragraph>
      </div>
    </div>
  );
}

export function StreamingIndicator() {
  return (
    <div style={{ padding: "8px 12px", display: "flex", alignItems: "center", gap: 8 }}>
      <QuestionCircleOutlined style={{ color: "#52c41a" }} />
      <LoadingOutlined style={{ fontSize: 14 }} />
    </div>
  );
}
