import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Login from "./auth/Login";
import Profile from "./auth/Profile";
import ProtectedRoute from "./auth/ProtectedRoute";
import "./index.css";
import axios from "axios";
import useAuth from "./auth/useAuth";
import Register from "./auth/Register";

const Home = () => {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedItems, setSelectedItems] = useState([]);

  const [user, setUser] = useState(null);
  const [myOrders, setMyOrders] = useState([]); // Sadece sipariş listesi için

  // Kullanıcı bilgisi çek
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) return;
      try {
        const res = await axios.get("http://localhost:8000/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
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
      if (!token || !user) return; // Kullanıcı yüklendikten sonra siparişleri çek
      try {
        const res = await axios.get(
          "http://localhost:8000/customer/my-orders",
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        setMyOrders(Array.isArray(res.data) ? res.data : []); // Gelen verinin dizi olduğundan emin ol
      } catch (err) {
        console.error("Sipariş bilgisi alınamadı.", err);
        setMyOrders([]); // Hata durumunda boş dizi ata
      }
    };
    if (user) {
      // Kullanıcı bilgisi varsa siparişleri çek
      fetchMyOrders();
    }
  }, [token, user]); // user bağımlılığını ekle

  // Menü + masaları çek
  useEffect(() => {
    const fetchPublicData = async () => {
      try {
        const [menuRes, tablesRes] = await Promise.all([
          // Yönlendirmeyi önlemek için sonuna / eklendi
          axios.get("http://localhost:8000/menu/"),
          axios.get("http://localhost:8000/manager/tables"),
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

  // Kullanıcının oturduğu masayı türet
  const myOccupiedTable =
    user && data?.tables
      ? data.tables.find((table) => table.current_user_id === user.id)
      : null;

  const handleSit = async (tableIdToSit) => {
    if (!token) {
      alert("Lütfen önce giriş yapın.");
      return;
    }
    if (myOccupiedTable) {
      alert(`Zaten Masa ${myOccupiedTable.number}'de oturuyorsunuz.`);
      return;
    }

    try {
      // Backend'e masaya oturma isteği gönder
      // Varsayım: POST /customer/sit endpoint'i { table_id: ... } bekliyor
      const response = await axios.post(
        `http://localhost:8000/customer/sit`,
        { table_id: tableIdToSit },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert(response.data.message || `Masaya başarıyla oturdunuz.`);

      // Oturulan masa ID'sini localStorage'a kaydet
      localStorage.setItem("current_table_id", tableIdToSit.toString());

      // Masa listesini yeniden çekerek UI'ı güncelle
      const tablesRes = await axios.get("http://localhost:8000/manager/tables");
      setData((prevData) => ({
        ...prevData,
        tables: tablesRes.data,
      }));
    } catch (err) {
      console.error("Masaya oturma hatası:", err);
      alert(
        err.response?.data?.detail || "Masaya oturulurken bir hata oluştu."
      );
    }
  };

  const handleAdd = (menuItemId) => {
    setSelectedItems((prevItems) => {
      const existing = prevItems.find(
        (item) => item.menu_item_id === menuItemId
      );
      if (existing) {
        return prevItems.map((item) =>
          item.menu_item_id === menuItemId
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      } else {
        return [
          ...prevItems,
          { menu_item_id: menuItemId, quantity: 1, note: "" },
        ];
      }
    });
  };

  const handleRemove = (menuItemId) => {
    setSelectedItems((prevItems) => {
      const existing = prevItems.find(
        (item) => item.menu_item_id === menuItemId
      );
      if (!existing) return prevItems;

      if (existing.quantity === 1) {
        return prevItems.filter((item) => item.menu_item_id !== menuItemId);
      } else {
        return prevItems.map((item) =>
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

    const tableId = localStorage.getItem("current_table_id");
    if (!tableId) {
      alert("Lütfen önce bir masaya oturun!");
      return;
    }

    try {
      const orderResponse = await axios.post(
        "http://localhost:8000/orders/", // Sondaki slash eklendi
        {
          table_id: parseInt(tableId),
          items: selectedItems,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      alert(orderResponse.data.message || "Sipariş başarıyla gönderildi!"); // Backend'den gelen mesajı kullan
      setSelectedItems([]);

      // Siparişten sonra siparişleri güncelle
      const updatedOrdersRes = await axios.get(
        "http://localhost:8000/customer/my-orders",
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setMyOrders(
        Array.isArray(updatedOrdersRes.data) ? updatedOrdersRes.data : []
      ); // Gelen verinin dizi olduğundan emin ol

      // Siparişten sonra menüyü de tekrar çek, stok durumları değişmiş olabilir
      const menuRes = await axios.get("http://localhost:8000/menu/");
      setData((prevData) => ({ ...prevData, menu_items: menuRes.data }));
    } catch (err) {
      console.error("Sipariş gönderme hatası:", err);
      // Hata mesajını backend'den alıp kullanıcıya gösterin
      alert(err.response?.data?.detail || "Sipariş gönderilirken hata oluştu.");
    }
  };

  // --- YENİ EKLENEN KISIM: ÖDEME İŞLEVİ ---
  const handlePayBill = async () => {
    // Sadece ödenmemiş siparişler varsa ödeme yapmaya izin ver
    const unpaidOrders = myOrders.filter((order) => !order.is_paid);

    if (unpaidOrders.length === 0) {
      alert("Ödenecek aktif bir siparişiniz bulunmamaktadır.");
      return;
    }

    // Toplam tutarı hesapla
    const totalAmount = unpaidOrders.reduce(
      (sum, order) => sum + order.total_amount,
      0
    );

    if (
      !window.confirm(
        `Toplam ${totalAmount}₺ ödeme yapmak istediğinize emin misiniz?`
      )
    ) {
      return; // Kullanıcı iptal ettiyse geri dön
    }

    try {
      // Backend'e ödeme isteği gönder
      // Varsayım: Backend'de /customer/pay-bill adında bir endpoint var ve tüm ödenmemiş siparişleri ödendi olarak işaretliyor.
      const res = await axios.post(
        "http://localhost:8000/customer/pay-bill",
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      alert(res.data.message || "Ödeme başarıyla tamamlandı!");

      // Ödeme sonrası siparişleri yeniden çekerek state'i güncelle
      const updatedOrdersRes = await axios.get(
        "http://localhost:8000/customer/my-orders",
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setMyOrders(
        Array.isArray(updatedOrdersRes.data) ? updatedOrdersRes.data : []
      ); // Gelen verinin dizi olduğundan emin ol
    } catch (err) {
      console.error("Ödeme işlemi sırasında hata oluştu:", err);
      alert(
        err.response?.data?.detail || "Ödeme işlemi sırasında bir hata oluştu."
      );
    }
  };
  // --- YENİ EKLENEN KISIM SONU ---

  if (loading) return <div>Yükleniyor...</div>;
  if (error) return <div style={{ color: "red" }}>{error}</div>;
  if (!data) return <div>Veri bulunamadı.</div>;

  // Stil tanımlamaları
  const styles = {
    container: {
      maxWidth: "900px",
      margin: "2rem auto",
      padding: "2rem",
      fontFamily: "Arial, sans-serif",
      color: "#333",
      backgroundColor: "#f9f9f9",
      borderRadius: "8px",
      boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
    },
    section: {
      marginBottom: "2.5rem",
      padding: "1.5rem",
      backgroundColor: "#fff",
      borderRadius: "8px",
      boxShadow: "0 1px 5px rgba(0,0,0,0.05)",
    },
    h2: {
      textAlign: "center",
      color: "#2c3e50",
      marginBottom: "2rem",
      borderBottom: "2px solid #e0e0e0",
      paddingBottom: "0.5rem",
    },
    h3: {
      color: "#34495e",
      marginBottom: "1rem",
      borderBottom: "1px solid #eee",
      paddingBottom: "0.5rem",
    },
    ul: { listStyleType: "none", paddingLeft: 0 },
    li: {
      marginBottom: "0.8rem",
      padding: "0.5rem",
      borderBottom: "1px solid #f0f0f0",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
    },
    button: {
      padding: "8px 15px",
      margin: "0 5px",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer",
      fontWeight: "bold",
      transition: "background-color 0.2s ease",
    },
    primaryButton: { backgroundColor: "#3498db", color: "white" },
    secondaryButton: { backgroundColor: "#e74c3c", color: "white" },
    actionButton: { backgroundColor: "#2ecc71", color: "white" },
    disabledButton: { backgroundColor: "#bdc3c7", cursor: "not-allowed" },
    itemQuantity: {
      marginLeft: "10px",
      fontWeight: "bold",
      minWidth: "70px",
      textAlign: "right",
    },
    tableStatus: { fontStyle: "italic", color: "#7f8c8d", marginLeft: "5px" },
    userInfo: {
      backgroundColor: "#ecf0f1",
      padding: "1.5rem",
      borderRadius: "8px",
      marginTop: "2rem",
    },
    selectedItemsSection: {
      marginTop: "2rem",
      padding: "1.5rem",
      backgroundColor: "#fff",
      borderRadius: "8px",
      boxShadow: "0 1px 5px rgba(0,0,0,0.05)",
    },
    billSummarySection: {
      marginTop: "2rem",
      padding: "1.5rem",
      border: "1px solid #3498db",
      borderRadius: "8px",
      backgroundColor: "#eaf5ff",
    },
    totalAmountText: {
      color: "#e74c3c",
      fontWeight: "bold",
      fontSize: "1.1em",
    },
    payButton: {
      backgroundColor: "#28a745",
      color: "white",
      padding: "12px 25px",
      fontSize: "1.1rem",
      marginTop: "1rem",
      width: "100%",
    },
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.h2}>🍽️ Restoran Yönetim Sistemi</h2>

      <section style={styles.section}>
        <h3 style={styles.h3}>📋 Menü</h3>
        <ul style={styles.ul}>
          {data.menu_items.map((m) => {
            const selected = selectedItems.find(
              (item) => item.menu_item_id === m.id
            );
            const quantity = selected ? selected.quantity : 0;

            return (
              <li key={m.id} style={styles.li}>
                <span>
                  {m.name} - {m.price}₺
                </span>
                {token &&
                  user?.role === "CUSTOMER" && ( // Sadece müşteri rolü sipariş verebilir
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <button
                        onClick={() => handleAdd(m.id)}
                        style={{
                          ...styles.button,
                          ...styles.primaryButton,
                          marginRight: "5px",
                        }}
                      >
                        +
                      </button>
                      <button
                        onClick={() => handleRemove(m.id)}
                        disabled={quantity === 0}
                        style={{
                          ...styles.button,
                          ...styles.secondaryButton,
                          ...(quantity === 0 && styles.disabledButton),
                        }}
                      >
                        -
                      </button>
                      <span style={styles.itemQuantity}>Adet: {quantity}</span>
                    </div>
                  )}
              </li>
            );
          })}
        </ul>
      </section>

      <section style={styles.section}>
        <h3 style={styles.h3}>🪑 Masalar</h3>
        <ul style={styles.ul}>
          {data.tables.map((t, i) => {
            const isCurrentUsersTable = myOccupiedTable?.id === t.id;
            const hasUnpaidOrder = myOrders.some(
              (o) => o.table_id === t.id && !o.is_paid
            );

            return (
              <li
                key={t.id || i}
                style={{
                  ...styles.li,
                  backgroundColor: isCurrentUsersTable
                    ? "#e8f4f8"
                    : "transparent",
                }}
              >
                <div>
                  Masa {t.number}{" "}
                  <span style={styles.tableStatus}>({t.status})</span>
                  {t.current_user_id && (
                    <span
                      style={{
                        marginLeft: "10px",
                        color: isCurrentUsersTable ? "#16a085" : "#2980b9",
                        fontWeight: isCurrentUsersTable ? "bold" : "normal",
                      }}
                    >
                      (Kullanıcı ID: {t.current_user_id}
                      {isCurrentUsersTable ? " - Siz" : ""})
                    </span>
                  )}
                </div>
                {token && user?.role === "CUSTOMER" && (
                  <div>
                    {isCurrentUsersTable ? (
                      <>
                        <button
                          onClick={async () => {
                            if (hasUnpaidOrder) {
                              alert(
                                "Ödenmemiş siparişiniz var, masadan kalkamazsınız."
                              );
                              return;
                            }

                            try {
                              const res = await axios.post(
                                `http://localhost:8000/customer/leave`,
                                {},
                                {
                                  headers: { Authorization: `Bearer ${token}` },
                                }
                              );
                              alert(res.data.message);
                              localStorage.removeItem("current_table_id");
                              // Masadan kalktıktan sonra myOrders'ı temizle (veya yeniden çek)
                              setMyOrders([]); // Eğer masadan kalkınca o masanın siparişleri artık gösterilmeyecekse
                              // Masaları ve menüyü de tekrar çekerek durumlarını güncelle
                              const [menuRes, tablesRes] = await Promise.all([
                                axios.get("http://localhost:8000/menu/"),
                                axios.get(
                                  "http://localhost:8000/manager/tables"
                                ), // Manager/tables hala token gerektirebilir
                              ]);
                              setData({
                                menu_items: menuRes.data,
                                tables: tablesRes.data,
                              });
                            } catch (err) {
                              alert(
                                err.response?.data?.detail || "Kalkma hatası."
                              );
                            }
                          }}
                          style={{
                            ...styles.button,
                            ...styles.secondaryButton,
                            ...(hasUnpaidOrder && styles.disabledButton),
                          }}
                          disabled={hasUnpaidOrder}
                        >
                          {hasUnpaidOrder ? "Ödeme Bekleniyor..." : "Kalk"}
                        </button>
                      </>
                    ) : (
                      !myOccupiedTable && // Kullanıcı başka bir masada oturmuyorsa
                      t.status === "AVAILABLE" && (
                        <button
                          onClick={() => handleSit(t.id)} // t.id gönderilmeli
                          style={{ ...styles.button, ...styles.actionButton }}
                        >
                          Otur
                        </button>
                      )
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      {token && user?.role === "CUSTOMER" && selectedItems.length > 0 && (
        <section style={styles.selectedItemsSection}>
          <h3 style={styles.h3}>🛒 Seçilen Ürünler</h3>
          {selectedItems.length === 0 ? (
            <p>Henüz ürün seçilmedi.</p>
          ) : (
            <ul>
              {selectedItems.map((item) => {
                const menuItem = data.menu_items.find(
                  (m) => m.id === item.menu_item_id
                );
                return (
                  <li key={item.menu_item_id} style={styles.li}>
                    {menuItem?.name} - Adet: {item.quantity}
                  </li>
                );
              })}
            </ul>
          )}

          <button
            onClick={handlePlaceOrder}
            disabled={selectedItems.length === 0}
            style={{
              ...styles.button,
              ...styles.actionButton,
              width: "100%",
              marginTop: "1rem",
              padding: "12px",
            }}
          >
            🛍️ Sipariş Ver
          </button>
        </section>
      )}

      {/* --- YENİ EKLENEN BÖLÜM: Müşteri Hesabı ve Ödeme Alanı --- */}
      {token &&
        user?.role === "CUSTOMER" &&
        myOccupiedTable &&
        myOrders.length > 0 &&
        (() => {
          const unpaidOrdersForCurrentTable = myOrders.filter(
            (order) => order.table_id === myOccupiedTable?.id && !order.is_paid
          );

          if (unpaidOrdersForCurrentTable.length === 0) {
            return (
              <section style={styles.billSummarySection}>
                <h3 style={styles.h3}>
                  💰 Hesap Özeti (Masa {myOccupiedTable?.number})
                </h3>
                <p>Bu masaya ait ödenmemiş siparişiniz bulunmamaktadır.</p>
              </section>
            );
          }

          return (
            <section style={styles.billSummarySection}>
              <h3 style={styles.h3}>
                💰 Hesap Özeti (Masa {myOccupiedTable?.number})
              </h3>
              <>
                <ul>
                  {unpaidOrdersForCurrentTable.map((order) => (
                    <li key={order.id} style={{ marginBottom: "0.5rem" }}>
                      Sipariş ID: **{order.id}** - Toplam Tutar: **
                      {order.total_amount}₺** - Durum:{" "}
                      {order.is_paid ? "✅ Ödendi" : "❌ Ödenmedi"}
                      {order.items.map((item) => {
                        return (
                          // Backend'den gelen item.name (sipariş anındaki ad) ve key için item.menu_item_id kullanılır.
                          <span
                            key={item.id} // Anahtar olarak item.id (OrderItem.id) kullanıldı
                            style={{
                              marginLeft: "10px",
                              fontSize: "0.9em",
                              color: "#555",
                            }}
                          >
                            ({item.name} x {item.quantity})
                          </span>
                        );
                      })}
                    </li>
                  ))}
                </ul>
                <h4>
                  Toplam Ödenmemiş Tutar:{" "}
                  <span style={styles.totalAmountText}>
                    {unpaidOrdersForCurrentTable
                      .reduce(
                        (sum, order) =>
                          sum + parseFloat(order.total_amount || 0),
                        0
                      )
                      .toFixed(2)}
                    ₺
                  </span>
                </h4>
                <button
                  onClick={handlePayBill}
                  disabled={unpaidOrdersForCurrentTable.length === 0}
                  style={{
                    ...styles.button,
                    ...styles.payButton,
                    ...(unpaidOrdersForCurrentTable.length === 0 &&
                      styles.disabledButton),
                  }}
                >
                  💳 Hesabı Öde
                </button>
              </>
            </section>
          );
        })()}
      {/* --- YENİ EKLENEN BÖLÜM SONU --- */}

      {token && user && (
        <div style={styles.userInfo}>
          <h3 style={styles.h3}>👤 Kullanıcı Bilgileri</h3>
          <p>
            <strong>ID:</strong> {user.id}
          </p>
          <p>
            <strong>Ad:</strong> {user.name}
          </p>
          <p>
            <strong>Email:</strong> {user.email}
          </p>
          <p>
            <strong>Rol:</strong> {user.role}
          </p>
        </div>
      )}
    </div>
  );
};

// Yönlendirme ayarları
const router = createBrowserRouter([
  { path: "/", element: <Home /> },
  { path: "/login", element: <Login /> },
  { path: "/register", element: <Register /> },
  {
    path: "/profile",
    element: (
      <ProtectedRoute>
        <Profile />
      </ProtectedRoute>
    ),
  },
]);

// Uygulamayı başlat
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
