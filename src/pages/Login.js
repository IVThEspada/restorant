import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../services/api';

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = await loginUser(username, password);
      localStorage.setItem('token', data.access_token);
      navigate('/');
    } catch (err) {
      setError('Giriş başarısız');
    }
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <h2 className="text-xl font-bold mb-4">Giriş Yap</h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input type="text" placeholder="Kullanıcı Adı" value={username} onChange={(e) => setUsername(e.target.value)} className="p-2 border rounded" />
        <input type="password" placeholder="Şifre" value={password} onChange={(e) => setPassword(e.target.value)} className="p-2 border rounded" />
        {error && <p className="text-red-500">{error}</p>}
        <button type="submit" className="bg-blue-500 text-white py-2 rounded">Giriş</button>
      </form>
    </div>
  );
};

export default Login;