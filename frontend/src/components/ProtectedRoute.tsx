import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div className="container" style={{ padding: "48px 0" }}>
        <p className="muted">Загрузка...</p>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
