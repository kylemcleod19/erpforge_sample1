import { CheckCircleFilled, CloseOutlined, RocketOutlined } from "@ant-design/icons";
import { Button, List, Progress, Typography } from "antd";
import React, { useEffect, useState } from "react";
import {
  dismissOnboarding,
  getProgress,
  Milestone,
  OnboardingProgress,
} from "../api/onboarding";

const { Text } = Typography;

interface OnboardingChecklistProps {
  onMilestoneClick?: (copilotPrompt: string) => void;
}

export default function OnboardingChecklist({ onMilestoneClick }: OnboardingChecklistProps) {
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    getProgress()
      .then((p) => {
        setProgress(p);
        if (p.dismissed) setDismissed(true);
      })
      .catch(() => {});
  }, []);

  if (dismissed || !progress || progress.total === 0) return null;
  if (progress.completed_count === progress.total) return null;

  const pct = Math.round((progress.completed_count / progress.total) * 100);

  const handleDismiss = async () => {
    setDismissed(true);
    await dismissOnboarding().catch(() => {});
  };

  return (
    <div
      style={{
        padding: "12px 16px",
        borderTop: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <Text style={{ color: "#fff", fontSize: 12, fontWeight: 600 }}>
          <RocketOutlined style={{ marginRight: 6 }} />
          Getting Started
        </Text>
        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          style={{ color: "#666" }}
          onClick={handleDismiss}
        />
      </div>

      <Progress
        percent={pct}
        size="small"
        strokeColor="#52c41a"
        trailColor="rgba(255,255,255,0.1)"
        format={() => (
          <Text style={{ color: "#aaa", fontSize: 11 }}>
            {progress.completed_count}/{progress.total}
          </Text>
        )}
      />

      <List
        size="small"
        dataSource={progress.milestones}
        style={{ marginTop: 4 }}
        renderItem={(m: Milestone) => (
          <div
            key={m.key}
            style={{
              padding: "4px 0",
              cursor: m.completed ? "default" : "pointer",
              opacity: m.completed ? 0.5 : 1,
            }}
            onClick={() => {
              if (!m.completed && onMilestoneClick) {
                onMilestoneClick(m.copilot_prompt);
              }
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <CheckCircleFilled
                style={{
                  color: m.completed ? "#52c41a" : "rgba(255,255,255,0.2)",
                  fontSize: 12,
                }}
              />
              <Text
                style={{
                  color: m.completed ? "#888" : "#ddd",
                  fontSize: 12,
                  textDecoration: m.completed ? "line-through" : "none",
                }}
              >
                {m.label}
              </Text>
            </div>
          </div>
        )}
      />
    </div>
  );
}
