import React, { useEffect, useState } from 'react';
import axios from 'axios';
import useAuth from '../auth/useAuth';

const ManagerDashboard = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const res = await axios.get('http://localhost:8000/manager/dashboard', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        setData(res.data);
      } catch (err) {
        console.error('Dashboard Error:', err);
        setError("Veri alınamadı. Yetkisiz giriş olabilir.");
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchDashboardData();
    }
  }, [token]);

  if (loading) return <div>Yükleniyor...</div>;
  if (error) return <div style={{ color: "red" }}>{error}</div>;
  if (!data) return <div>Veri bulunamadı.</div>;

  return (
    <div style={{ maxWidth: '800px', margin: 'auto', padding: '2rem' }}>
      <h2>📊 Yönetici Paneli</h2>

      <section>
        <h3>👥 Kullanıcılar</h3>
        <ul>
          {data.users.map((u, index) => (
            <li key={u.id || index}>{u.email} ({u.role})</li>
          ))}
        </ul>
      </section>

      <section>
        <h3>📋 Menü</h3>
        <ul>
          {data.menu_items.map((m, index) => (
            <li key={m.id || index}>{m.name} - {m.price}₺</li>
          ))}
        </ul>
      </section>

      <section>
        <h3>🍅 Malzemeler</h3>
        <ul>
          {data.ingredients.map((i, index) => (
            <li key={i.id || index}>{i.name} ({i.stock_quantity} stok)</li>
          ))}
        </ul>
      </section>

      <section>
        <h3>🍽️ Masalar</h3>
        <ul>
          {data.tables.map((t, index) => (
            <li key={t.id || index}>Masa {t.number} ({t.status})</li>
          ))}
        </ul>
      </section>

      <section>
        <h3>🕒 Vardiyalar</h3>
        <ul>
          {data.schedules.map((s, index) => (
            <li key={s.id || index}>User ID {s.user_id} - {s.work_date}</li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default ManagerDashboard;
