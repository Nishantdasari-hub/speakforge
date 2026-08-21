import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import AdminDashboard from "./pages/AdminDashboard";
import AdminTests from "./pages/AdminTests";
import AdminQuestions from "./pages/AdminQuestions";
import AdminAnalytics from "./pages/AdminAnalytics";
import TestReport from "./pages/TestReport";
import Tests from "./pages/Tests";
import UserTests from "./pages/UserTests";
import TestDetail from "./pages/TestDetail";
import UserDashboard from "./pages/UserDashboard";
import MyResults from "./pages/MyResults";

import ProtectedRoute from "./components/ProtectedRoute";
import MainLayout from "./layout/MainLayout";

function App() {
  return (
    <BrowserRouter>

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
            <ProtectedRoute>
              <MainLayout>
                <AdminDashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/admin/tests"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AdminTests />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/questions"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AdminQuestions />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="/report/:testId" element={<TestReport />} />
        <Route
          path="/admin/analytics"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AdminAnalytics />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route path="/my-results" element={<MyResults />} />        
      </Routes>

    </BrowserRouter>
  );
}

export default App;