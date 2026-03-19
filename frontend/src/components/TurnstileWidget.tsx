import { Turnstile, TurnstileInstance } from "@marsidev/react-turnstile";
import { forwardRef } from "react";

const SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY ?? "";

interface Props {
  onSuccess: (token: string) => void;
  onExpire?: () => void;
}

const TurnstileWidget = forwardRef<TurnstileInstance, Props>(({ onSuccess, onExpire }, ref) => {
  if (!SITE_KEY) return null;
  return (
    <Turnstile
      ref={ref}
      siteKey={SITE_KEY}
      options={{ appearance: "interaction-only", execution: "render" }}
      onSuccess={onSuccess}
      onExpire={onExpire}
    />
  );
});
TurnstileWidget.displayName = "TurnstileWidget";
export default TurnstileWidget;
