import type { ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/auth/AuthProvider";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Chat from "@/pages/Chat";
import Leaves from "@/pages/Leaves";
import Employees from "@/pages/Employees";
import AgentConsole from "@/pages/AgentConsole";
import Policies from "@/pages/Policies";
import Settings from "@/pages/Settings";
import { Spinner } from "@/components/ui";

function AdminRoute({ children }: { children: ReactElement }) {
  const { me } = useAuth();
  return me?.role === "admin" ? children : <Navigate to="/chat" replace />;
}

function Shell() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner />
      </div>
    );
  }
  if (!session) return <Login />;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/chat" element={<Chat />} />
        <Route path="/leaves" element={<Leaves />} />
        <Route path="/policies" element={<Policies />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/employees" element={<AdminRoute><Employees /></AdminRoute>} />
        <Route path="/console" element={<AdminRoute><AgentConsole /></AdminRoute>} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </BrowserRouter>
  );
}
