import { useCallback, useEffect, useState } from "react";

export type ToastKind = "success" | "error";

export function useToast(durationMs = 4000) {
  const [toast, setToast] = useState<{ message: string; kind: ToastKind } | null>(null);

  const showToast = useCallback((message: string, kind: ToastKind = "success") => {
    setToast({ message, kind });
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), durationMs);
    return () => clearTimeout(timer);
  }, [toast, durationMs]);

  return { toast, showToast, clearToast };
}
