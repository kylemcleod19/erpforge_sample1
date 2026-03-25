import { RocketOutlined } from "@ant-design/icons";
import { Button, Empty, Typography } from "antd";
import React from "react";

const { Paragraph, Text } = Typography;

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  workflowHint?: string;
}

export default function EmptyState({ title, description, actionLabel, onAction, workflowHint }: EmptyStateProps) {
  return (
    <div style={{ textAlign: "center", padding: "80px 0" }}>
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <div>
            <Text strong style={{ fontSize: 16, display: "block", marginBottom: 8 }}>
              {title}
            </Text>
            <Paragraph type="secondary" style={{ maxWidth: 400, margin: "0 auto" }}>
              {description}
            </Paragraph>
          </div>
        }
      >
        {workflowHint && (
          <Paragraph
            type="secondary"
            style={{
              maxWidth: 440,
              margin: "0 auto 16px",
              fontSize: 12,
              background: "#fafafa",
              padding: "8px 16px",
              borderRadius: 6,
            }}
          >
            <RocketOutlined style={{ marginRight: 6 }} />
            {workflowHint}
          </Paragraph>
        )}
        {actionLabel && onAction && (
          <Button type="primary" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </Empty>
    </div>
  );
}
