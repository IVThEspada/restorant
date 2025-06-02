// src/auth/ProtectedRoute.js
import React from "react";
import { Navigate } from "react-router-dom";
import useAuth from "./useAuth";

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return children;
};

export default ProtectedRoute;
