import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const Login = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post("http://localhost:8000/auth/login", {
                email: email,
                password: password
            }, {
                headers: {
                    "Content-Type": "application/json"
                }
            });

            const token = response.data.access_token;
            localStorage.setItem("token", token);
            navigate("/profile");
        } catch (err) {
            console.error("Giriş hatası:", err.response?.data || err.message);
            setError("Giriş başarısız: E-posta veya şifre hatalı.");
        }
    };

    return (
        <div style={{ maxWidth: "400px", margin: "auto", marginTop: "100px" }}>
            <h2>Giriş Yap</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>E-posta</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Şifre</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit">Giriş Yap</button>
            </form>
            {error && <p style={{ color: "red" }}>{error}</p>}
        </div>
    );
};

export default Login;
