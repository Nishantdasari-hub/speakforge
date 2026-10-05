import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));
const AdminTests = lazy(() => import("./pages/AdminTests"));
const AdminQuestions = lazy(() => import("./pages/AdminQuestions"));
const AdminAnalytics = lazy(() => import("./pages/AdminAnalytics"));
const TestReport = lazy(() => import("./pages/TestReport"));

const UserTests = lazy(() => import("./pages/UserTests"));
const TestDetail = lazy(() => import("./pages/TestDetail"));
const UserDashboard = lazy(() => import("./pages/UserDashboard"));
const MyResults = lazy(() => import("./pages/MyResults"));

import ProtectedRoute from "./components/ProtectedRoute";
import MainLayout from "./layout/MainLayout";

function App() {
  return (
    <BrowserRouter>

      <Suspense fallback={<p role="status" className="p-8 text-white">Loading page...</p>}>
      <Routes>

        {/* PUBLIC ROUTES */}

        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />


        {/* USER ROUTES */}

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <UserDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/tests"
          element={
            <ProtectedRoute>
              <UserTests />
            </ProtectedRoute>
          }
        />

        <Route
          path="/test/:id"
          element={
            <ProtectedRoute>
              <TestDetail />
            </ProtectedRoute>
          }
        />


        {/* ADMIN ROUTES */}

        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute adminOnly>
              <MainLayout>
                <AdminDashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/tests"
          element={
            <ProtectedRoute adminOnly>
              <MainLayout>
                <AdminTests />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/questions"
          element={
            <ProtectedRoute adminOnly>
              <MainLayout>
                <AdminQuestions />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="/report/:testId" element={<ProtectedRoute><TestReport /></ProtectedRoute>} />
        <Route
          path="/admin/analytics"
          element={
            <ProtectedRoute adminOnly>
              <MainLayout>
                <AdminAnalytics />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route path="/my-results" element={<ProtectedRoute><MyResults /></ProtectedRoute>} />
        <Route path="*" element={<div className="p-8 text-white">Page not found. <a href="/dashboard">Go to Dashboard</a></div>} />
      </Routes>
      </Suspense>

    </BrowserRouter>
  );
}

export default App;
