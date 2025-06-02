import React, { useEffect, useState } from "react";
import axios from "axios";
import useAuth from "./useAuth";
import { useNavigate } from "react-router-dom";

const Profile = () => {
    const { token, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const response = await axios.get("http://localhost:8000/auth/me", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setUser(response.data);
            } catch (err) {
                console.error("Kullanıcı bilgileri alınamadı:", err);
                setError("Kullanıcı bilgileri alınamadı.");
            } finally {
                setLoading(false);
            }
        };

        // Eğer giriş yapılmışsa user'ı çek
        if (isAuthenticated && token) {
            fetchUser();
        } else {
            // Giriş yapılmamışsa hata yaz, başka fetch yapma
            setError("Kullanıcı bilgileri alınamadı.");
            setLoading(false);
        }
    }, [isAuthenticated, token]);

    const handleLogout = () => {
        logout();
        navigate("/login");
        // Logout olunca oturulan masayı sil
        // localStorage.removeItem('current_table_id');
    };

    if (loading) return <p>Yükleniyor...</p>;
    if (error) return <p style={{ color: "red" }}>{error}</p>;

    return (
        <div style={{ maxWidth: "600px", margin: "auto", marginTop: "50px" }}>
            <h2>Profil Bilgileri</h2>
            {user && (
                <div>
                    <p><strong>Ad:</strong> {user.name}</p>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Rol:</strong> {user.role}</p>
                    <button onClick={handleLogout}>Çıkış Yap</button>
                </div>
            )}
        </div>
    );
};

export default Profile;
