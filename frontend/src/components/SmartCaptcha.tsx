import { useEffect, useRef } from "react";

// Sitekey берётся из переменной окружения, чтобы не хардкодить под один проект.
const SITEKEY = import.meta.env.VITE_SMARTCAPTCHA_SITEKEY ?? "";

declare global {
  interface Window {
    smartCaptcha?: {
      render: (
        el: HTMLElement,
        opts: { sitekey: string; callback?: (t: string) => void; "expired-callback"?: () => void }
      ) => number;
      destroy?: (id: number) => void;
    };
  }
}

// Виджет Яндекс SmartCaptcha. onToken вызывается с токеном после прохождения.
// Если sitekey не задан — капча отключена, сразу отдаём «пройдено» (dev/local).
export function SmartCaptcha({ onToken }: { onToken: (token: string) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const widgetId = useRef<number | null>(null);
  const cb = useRef(onToken);
  cb.current = onToken;

  useEffect(() => {
    if (!SITEKEY) {
      cb.current("dev-bypass");
      return;
    }
    let cancelled = false;
    let timer: number | undefined;

    const tryRender = () => {
      if (cancelled || !ref.current || widgetId.current !== null) return;
      if (!window.smartCaptcha) {
        timer = window.setTimeout(tryRender, 200); // ждём загрузки captcha.js (defer)
        return;
      }
      widgetId.current = window.smartCaptcha.render(ref.current, {
        sitekey: SITEKEY,
        callback: (token: string) => cb.current(token),
        "expired-callback": () => cb.current(""),
      });
    };
    tryRender();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      if (widgetId.current !== null) window.smartCaptcha?.destroy?.(widgetId.current);
      widgetId.current = null;
    };
  }, []);

  if (!SITEKEY) return null;

  return (
    <div ref={ref} className="smart-captcha" data-sitekey={SITEKEY} style={{ minHeight: 100 }} />
  );
}
