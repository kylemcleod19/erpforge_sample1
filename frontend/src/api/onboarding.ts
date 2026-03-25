import client from "./client";

export interface Milestone {
  key: string;
  label: string;
  description: string;
  completed: boolean;
  copilot_prompt: string;
}

export interface OnboardingProgress {
  milestones: Milestone[];
  total: number;
  completed_count: number;
  dismissed: boolean;
}

export async function getProgress(): Promise<OnboardingProgress> {
  const { data } = await client.get<OnboardingProgress>("/onboarding/progress");
  return data;
}

export async function dismissOnboarding(): Promise<void> {
  await client.post("/onboarding/dismiss");
}

export async function refreshProgress(): Promise<OnboardingProgress> {
  const { data } = await client.post<OnboardingProgress>("/onboarding/refresh");
  return data;
}
