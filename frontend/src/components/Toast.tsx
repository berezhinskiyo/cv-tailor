import type { ToastKind } from "../hooks/useToast";

type Props = {
  message: string;
  kind: ToastKind;
  onClose: () => void;
};

export function Toast({ message, kind, onClose }: Props) {
  return (
    <div className={`toast toast-${kind}`} role="status" aria-live="polite">
      <span>{message}</span>
      <button type="button" className="toast-close" onClick={onClose} aria-label="Закрыть">
        ×
      </button>
    </div>
  );
}
