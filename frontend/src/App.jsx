import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Camera from "./pages/Camera";
import Recommendations from "./pages/Recommendations";

import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Public routes */}

        <Route
          path="/"
          element={<Navigate to="/login" replace />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        {/* Protected routes */}

        <Route element={<ProtectedRoute />}>

          <Route
            path="/camera"
            element={<Camera />}
          />

          <Route
            path="/recommendations"
            element={<Recommendations />}
          />

        </Route>

        {/* Unknown route */}

        <Route
          path="*"
          element={<Navigate to="/login" replace />}
        />

      </Routes>
    </BrowserRouter>
  );
}