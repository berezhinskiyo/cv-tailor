import { Navigate, Route, Routes } from "react-router-dom";

import { CookieBanner } from "./components/CookieBanner";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { DashboardPage } from "./pages/DashboardPage";
import { LandingPage } from "./pages/LandingPage";
import { OfferPage } from "./pages/OfferPage";
import { PrivacyPage } from "./pages/PrivacyPage";
import { ContactsPage } from "./pages/ContactsPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/offer" element={<OfferPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route path="/auth/oauth/callback" element={<OAuthCallbackPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <CookieBanner />
    </AuthProvider>
  );
}
