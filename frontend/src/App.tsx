import type { ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/auth/AuthProvider";
import { ToastProvider } from "@/components/Toast";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Chat from "@/pages/Chat";
import Leaves from "@/pages/Leaves";
import Attendance from "@/pages/Attendance";
import Payroll from "@/pages/Payroll";
import Expenses from "@/pages/Expenses";
import Announcements from "@/pages/Announcements";
import Employees from "@/pages/Employees";
import AgentConsole from "@/pages/AgentConsole";
import Analytics from "@/pages/Analytics";
import Policies from "@/pages/Policies";
import Helpdesk from "@/pages/Helpdesk";
import Settings from "@/pages/Settings";
import { Spinner } from "@/components/ui";

function AdminRoute({ children }: { children: ReactElement }) {
  const { me } = useAuth();
  return me?.role === "admin" ? children : <Navigate to="/dashboard" replace />;
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
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/leaves" element={<Leaves />} />
        <Route path="/attendance" element={<Attendance />} />
        <Route path="/payroll" element={<Payroll />} />
        <Route path="/expenses" element={<Expenses />} />
        <Route path="/announcements" element={<Announcements />} />
        <Route path="/policies" element={<Policies />} />
        <Route path="/helpdesk" element={<Helpdesk />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/employees" element={<AdminRoute><Employees /></AdminRoute>} />
        <Route path="/analytics" element={<AdminRoute><Analytics /></AdminRoute>} />
        <Route path="/console" element={<AdminRoute><AgentConsole /></AdminRoute>} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Shell />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
