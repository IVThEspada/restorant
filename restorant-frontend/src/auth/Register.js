import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await axios.post('http://localhost:8000/auth/register', {
        name,
        email,
        password,
      });
      console.log(response.data);
      alert('Kayıt başarılı! Giriş yapabilirsiniz.');
      navigate('/login');
    } catch (err) {
      console.error('Register error:', err);
      setError(err.response?.data?.detail || 'Bir hata oluştu.');
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: 'auto', padding: '2rem' }}>
      <h2>📝 Kayıt Ol</h2>
      <form onSubmit={handleRegister}>
        <div>
          <label>Adınız:</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div>
          <label>E-posta:</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <label>Şifre:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <p style={{ color: 'red' }}>{error}</p>}

        <button type="submit">Kayıt Ol</button>
      </form>
    </div>
  );
};

export default Register;
