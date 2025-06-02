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
          // BURAYI KONTROL ETTİK: Zaten doğru endpoint'i kullanıyorsunuz!
          axios.get('http://localhost:8000/menu'),
          axios.get('http://localhost:8000/manager/tables'), // Manager/tables hala token gerektirebilir
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
  }, [token]); // token bağımlılığını ekledim, eğer manager/tables token gerektiriyorsa sayfa yüklendiğinde fetch yapılır.

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

      // Ayrıca masaları ve menüyü de güncelle
      const [menuRes, tablesRes] = await Promise.all([
        // BURAYI DEĞİŞTİRDİK: handleSit içinde de /menu endpoint'ini kullanıyoruz
        axios.get('http://localhost:8000/menu'),
        axios.get('http://localhost:8000/manager/tables'), // Manager/tables hala token gerektirebilir
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

      // Siparişten sonra menüyü de tekrar çek, stok durumları değişmiş olabilir
      const menuRes = await axios.get('http://localhost:8000/menu');
      setData(prevData => ({ ...prevData, menu_items: menuRes.data }));


    } catch (err) {
      console.error("Sipariş gönderme hatası:", err);
      alert("Sipariş gönderilirken hata oluştu.");
    }
  };

  // --- YENİ EKLENEN KISIM: ÖDEME İŞLEVİ ---
  const handlePayBill = async () => {
    // Sadece ödenmemiş siparişler varsa ödeme yapmaya izin ver
    const unpaidOrders = myOrders.orders.filter(order => !order.is_paid);

    if (unpaidOrders.length === 0) {
      alert("Ödenecek aktif bir siparişiniz bulunmamaktadır.");
      return;
    }

    // Toplam tutarı hesapla
    const totalAmount = unpaidOrders.reduce((sum, order) => sum + order.total_amount, 0);

    if (!window.confirm(`Toplam ${totalAmount}₺ ödeme yapmak istediğinize emin misiniz?`)) {
      return; // Kullanıcı iptal ettiyse geri dön
    }

    try {
      // Backend'e ödeme isteği gönder
      // Varsayım: Backend'de /customer/pay-bill adında bir endpoint var ve tüm ödenmemiş siparişleri ödendi olarak işaretliyor.
      const res = await axios.post('http://localhost:8000/customer/pay-bill', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert(res.data.message || "Ödeme başarıyla tamamlandı!");

      // Ödeme sonrası siparişleri yeniden çekerek state'i güncelle
      const updatedOrdersRes = await axios.get('http://localhost:8000/customer/my-orders', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyOrders(updatedOrdersRes.data);

    } catch (err) {
      console.error("Ödeme işlemi sırasında hata oluştu:", err);
      alert(err.response?.data?.detail || "Ödeme işlemi sırasında bir hata oluştu.");
    }
  };
  // --- YENİ EKLENEN KISIM SONU ---

  if (loading) return <div>Yükleniyor...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!data) return <div>Veri bulunamadı.</div>;

  return (
    <div style={{ maxWidth: '800px', margin: 'auto', padding: '2rem' }}>
      <h2>📊 Veritabanı İçeriği</h2>

      <section>
        <h3>📋 Menü</h3>
        <ul>
          {/* Backend'den sadece is_available=True olanlar geldiği için,
              burada ek bir is_available kontrolüne gerek kalmaz.
              Ancak, eğer menü öğesini pasifken gri göstermek isterseniz,
              MenuItemOut şemanıza is_available'ı ekleyip burada kullanabilirsiniz.
              Şimdilik, basitçe sadece mevcut olanları listeliyoruz. */}
          {data.menu_items.map((m) => {
            const selected = selectedItems.find(item => item.menu_item_id === m.id);
            const quantity = selected ? selected.quantity : 0;

            // Eğer is_available backend'den geliyorsa ve gri göstermek istiyorsanız:
            // MenuItemOut şemanızda is_available alanının olduğundan emin olun
            // if (m.is_available === false) { // Eğer backend'den gelen m.is_available kontrolü varsa
            //   return (
            //     <li key={m.id} style={{ color: '#aaa', textDecoration: 'line-through' }}>
            //       {m.name} - {m.price}₺ (Stokta Yok)
            //     </li>
            //   );
            // }

            return (
              <li key={m.id}>
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
                              // Masadan kalktıktan sonra myOrders'ı temizle veya boş bir duruma getir
                              setMyOrders({ table_number: null, orders: [] });
                              // Masaları ve menüyü de tekrar çekerek durumlarını güncelle
                              const [menuRes, tablesRes] = await Promise.all([
                                axios.get('http://localhost:8000/menu'), // BURAYI DA DEĞİŞTİRDİK
                                axios.get('http://localhost:8000/manager/tables'), // Manager/tables hala token gerektirebilir
                              ]);
                              setData({
                                menu_items: menuRes.data,
                                tables: tablesRes.data,
                              });

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

      {/* --- YENİ EKLENEN BÖLÜM: Müşteri Hesabı ve Ödeme Alanı --- */}
      {token && myOrders.table_number && myOrders.orders.length > 0 && (
        <section style={{ marginTop: "2rem", padding: "1.5rem", border: "1px solid #ddd", borderRadius: "8px", backgroundColor: "#f9f9f9" }}>
          <h3>💰 Hesap Özeti (Masa {myOrders.table_number})</h3>
          {myOrders.orders.length > 0 ? (
            <>
              <ul>
                {myOrders.orders.map(order => (
                  <li key={order.id} style={{ marginBottom: "0.5rem" }}>
                    Sipariş ID: **{order.id}** - Toplam Tutar: **{order.total_amount}₺** - Durum: {order.is_paid ? '✅ Ödendi' : '❌ Ödenmedi'}
                    {order.items.map(item => {
                        const menuItem = data.menu_items.find(m => m.id === item.menu_item_id);
                        return (
                            <span key={item.id} style={{marginLeft: "10px", fontSize: "0.9em", color: "#555"}}>
                                ({menuItem?.name} x {item.quantity})
                            </span>
                        );
                    })}
                  </li>
                ))}
              </ul>
              <h4>
                Toplam Ödenmemiş Tutar:{" "}
                <span style={{ color: "red", fontWeight: "bold" }}>
                  {myOrders.orders.filter(o => !o.is_paid).reduce((sum, order) => sum + order.total_amount, 0).toFixed(2)}₺
                </span>
              </h4>
              <button
                onClick={handlePayBill}
                disabled={myOrders.orders.filter(o => !o.is_paid).length === 0}
                style={{
                  padding: "10px 20px",
                  fontSize: "1rem",
                  backgroundColor: "#28a745",
                  color: "white",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                  marginTop: "1rem"
                }}
              >
                💳 Hesabı Öde
              </button>
            </>
          ) : (
            <p>Bu masaya ait henüz siparişiniz bulunmamaktadır.</p>
          )}
        </section>
      )}
      {/* --- YENİ EKLENEN BÖLÜM SONU --- */}


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