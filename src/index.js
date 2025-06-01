import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Login from './auth/Login';
import Profile from './auth/Profile';
import ProtectedRoute from './auth/ProtectedRoute';
import './index.css';
import axios from 'axios';
import useAuth from './auth/useAuth';
import Register from './auth/Register';

const Home = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedItems, setSelectedItems] = useState([]);

  const [user, setUser] = useState(null);
  const [myOrders, setMyOrders] = useState({ table_number: null, orders: [] });

  // Kullanıcı bilgisi çek
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) return;
      try {
        const res = await axios.get('http://localhost:8000/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(res.data);
      } catch (err) {
        console.error("Kullanıcı bilgisi alınamadı:", err);
      }
    };
    fetchUser();
  }, [token]);

  // Sipariş bilgisi çek
  useEffect(() => {
    const fetchMyOrders = async () => {
      if (!token) return;
      try {
        const res = await axios.get('http://localhost:8000/customer/my-orders', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setMyOrders(res.data);
      } catch (err) {
        console.error("Sipariş bilgisi alınamadı.", err);
      }
    };
    fetchMyOrders();
  }, [token]);

  // Menü + masaları çek
  useEffect(() => {
    const fetchPublicData = async () => {
      try {
        const [menuRes, tablesRes] = await Promise.all([
          axios.get('http://localhost:8000/manager/menu'),
          axios.get('http://localhost:8000/manager/tables'),
        ]);
        setData({
          menu_items: menuRes.data,
          tables: tablesRes.data,
        });
      } catch (err) {
        setError("Veri alınamadı.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPublicData();
  }, []);

  const handleSit = async (tableNumber) => {
  try {
    const res = await axios.post(`http://localhost:8000/customer/sit/${tableNumber}`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    alert(res.data.message);
    localStorage.setItem('current_table_id', tableNumber);

    // 🔥 Ekledik: myOrders güncelle!
    const myOrdersRes = await axios.get('http://localhost:8000/customer/my-orders', {
      headers: { Authorization: `Bearer ${token}` }
    });
    setMyOrders(myOrdersRes.data);

    // Ayrıca masaları da güncelle (opsiyonel)
    const [menuRes, tablesRes] = await Promise.all([
      axios.get('http://localhost:8000/manager/menu'),
      axios.get('http://localhost:8000/manager/tables'),
    ]);
    setData({
      menu_items: menuRes.data,
      tables: tablesRes.data,
    });

  } catch (err) {
    alert(err.response?.data?.detail || "Bir hata oluştu.");
  }
};


  const handleAdd = (menuItemId) => {
    setSelectedItems(prevItems => {
      const existing = prevItems.find(item => item.menu_item_id === menuItemId);
      if (existing) {
        return prevItems.map(item =>
          item.menu_item_id === menuItemId
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      } else {
        return [...prevItems, { menu_item_id: menuItemId, quantity: 1, note: "" }];
      }
    });
  };

  const handleRemove = (menuItemId) => {
    setSelectedItems(prevItems => {
      const existing = prevItems.find(item => item.menu_item_id === menuItemId);
      if (!existing) return prevItems;

      if (existing.quantity === 1) {
        return prevItems.filter(item => item.menu_item_id !== menuItemId);
      } else {
        return prevItems.map(item =>
          item.menu_item_id === menuItemId
            ? { ...item, quantity: item.quantity - 1 }
            : item
        );
      }
    });
  };

  const handlePlaceOrder = async () => {
    if (selectedItems.length === 0) {
      alert("Lütfen en az 1 ürün seçiniz.");
      return;
    }

    const tableId = localStorage.getItem('current_table_id');
    if (!tableId) {
      alert("Lütfen önce bir masaya oturun!");
      return;
    }

    try {
      await axios.post('http://localhost:8000/orders', {
        table_id: parseInt(tableId),
        items: selectedItems
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert("Sipariş başarıyla gönderildi!");
      setSelectedItems([]);

      // Siparişten sonra siparişleri güncelle
      const res = await axios.get('http://localhost:8000/customer/my-orders', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyOrders(res.data);

    } catch (err) {
      console.error("Sipariş gönderme hatası:", err);
      alert("Sipariş gönderilirken hata oluştu.");
    }
  };

  if (loading) return <div>Yükleniyor...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!data) return <div>Veri bulunamadı.</div>;

  return (
    <div style={{ maxWidth: '800px', margin: 'auto', padding: '2rem' }}>
      <h2>📊 Veritabanı İçeriği</h2>

      <section>
        <h3>📋 Menü</h3>
        <ul>
          {data.menu_items.map((m, i) => {
            const selected = selectedItems.find(item => item.menu_item_id === m.id);
            const quantity = selected ? selected.quantity : 0;

            return (
              <li key={m.id || i}>
                {m.name} - {m.price}₺
                {token && (
                  <>
                    <button onClick={() => handleAdd(m.id)}>➕</button>
                    <button onClick={() => handleRemove(m.id)} disabled={quantity === 0}>➖</button>
                    <span style={{ marginLeft: "10px" }}>Adet: {quantity}</span>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <section>
  <h3>🍽️ Masalar</h3>
  <ul>
    {data.tables.map((t, i) => {
      const isMyTable = myOrders.table_number === t.number;
      const hasUnpaidOrder = myOrders.orders.some(o => !o.is_paid);
      const isAnyTableOccupiedByMe = myOrders.table_number !== null;

      return (
        <li key={t.id || i}>
          Masa {t.number} ({t.status})
          {t.current_user_id && (
            <span style={{ marginLeft: '10px', color: 'green' }}>
              (Kullanıcı: {t.current_user_id})
            </span>
          )}
          {token && (
            <>
              {isMyTable ? (
                <>
                  <button
                    onClick={async () => {
                      if (hasUnpaidOrder) {
                        alert("Ödenmemiş siparişiniz var, masadan kalkamazsınız.");
                        return;
                      }

                      try {
                        const res = await axios.post(`http://localhost:8000/customer/leave`, {}, {
                          headers: { Authorization: `Bearer ${token}` }
                        });
                        alert(res.data.message);
                        localStorage.removeItem('current_table_id');
                      } catch (err) {
                        alert(err.response?.data?.detail || "Kalkma hatası.");
                      }
                    }}
                    style={{ marginLeft: "10px" }}
                    disabled={hasUnpaidOrder}
                  >
                    {hasUnpaidOrder ? "Ödeme Bekleniyor..." : "Kalk"}
                  </button>
                </>
              ) : (
                // 🔥 Burayı değiştirdik:
                !isAnyTableOccupiedByMe && t.status === "AVAILABLE" && (
                  <button onClick={() => handleSit(t.number)} style={{ marginLeft: "10px" }}>
                    Otur
                  </button>
                )
              )}
            </>
          )}
        </li>
      );
    })}
  </ul>
</section>

      {token && (
        <section style={{ marginTop: "2rem" }}>
          <h3>🛒 Seçilen Ürünler</h3>
          {selectedItems.length === 0 ? (
            <p>Henüz ürün seçilmedi.</p>
          ) : (
            <ul>
              {selectedItems.map(item => {
                const menuItem = data.menu_items.find(m => m.id === item.menu_item_id);
                return (
                  <li key={item.menu_item_id}>
                    {menuItem?.name} - Adet: {item.quantity}
                  </li>
                );
              })}
            </ul>
          )}

          <button onClick={handlePlaceOrder} disabled={selectedItems.length === 0}>
            🛍️ Sipariş Ver
          </button>
        </section>
      )}

      {token && user && (
        <div style={{ marginTop: "2rem", padding: "1rem", borderTop: "1px solid #ccc" }}>
          <h3>👤 Giriş Yapan Kullanıcı</h3>
          <p><strong>ID:</strong> {user.id}</p>
          <p><strong>Ad:</strong> {user.name}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Rol:</strong> {user.role}</p>
        </div>
      )}
    </div>
  );
};

// Yönlendirme ayarları
const router = createBrowserRouter([
  { path: '/', element: <Home /> },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  {
    path: '/profile',
    element: (
      <ProtectedRoute>
        <Profile />
      </ProtectedRoute>
    ),
  },
]);

// Uygulamayı başlat
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
