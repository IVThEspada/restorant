// src/auth/useAuth.js
import { useEffect, useState } from "react";

const useAuth = () => {
    const [token, setToken] = useState(localStorage.getItem("token"));
    const [isAuthenticated, setIsAuthenticated] = useState(!!token);

    useEffect(() => {
        const storedToken = localStorage.getItem("token");
        setToken(storedToken);
        setIsAuthenticated(!!storedToken);
    }, []);

    const login = (newToken) => {
        localStorage.setItem("token", newToken);
        setToken(newToken);
        setIsAuthenticated(true);
    };

    const logout = () => {
        localStorage.removeItem("token");
        setToken(null);
        setIsAuthenticated(false);
    };

    return {
        token,
        isAuthenticated,
        login,
        logout,
    };
};

export default useAuth;
