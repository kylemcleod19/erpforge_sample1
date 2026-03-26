import { InboxOutlined, RocketOutlined } from "@ant-design/icons";
import { Button, Typography } from "antd";
import React from "react";

const { Paragraph, Title, Text } = Typography;

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  workflowHint?: string;
  icon?: React.ReactNode;
}

export default function EmptyState({ title, description, actionLabel, onAction, workflowHint, icon }: EmptyStateProps) {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "60px 24px" }}>
      <div
        style={{
          maxWidth: 520,
          width: "100%",
          background: "#fff",
          border: "1px solid #f0f0f0",
          borderLeft: "4px solid #1677ff",
          borderRadius: 8,
          padding: "32px 32px 24px",
        }}
      >
        <div style={{ marginBottom: 16, fontSize: 36, color: "#1677ff", lineHeight: 1 }}>
          {icon || <InboxOutlined />}
        </div>

        <Title level={4} style={{ margin: 0, marginBottom: 8 }}>
          {title}
        </Title>

        <Paragraph type="secondary" style={{ marginBottom: workflowHint ? 16 : 20 }}>
          {description}
        </Paragraph>

        {workflowHint && (
          <div
            style={{
              background: "#f6ffed",
              border: "1px solid #b7eb8f",
              padding: "10px 16px",
              borderRadius: 6,
              marginBottom: 20,
              fontSize: 13,
            }}
          >
            <RocketOutlined style={{ marginRight: 6, color: "#52c41a" }} />
            <Text type="secondary">{workflowHint}</Text>
          </div>
        )}

        {actionLabel && onAction && (
          <Button type="primary" size="large" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </div>
    </div>
  );
}
