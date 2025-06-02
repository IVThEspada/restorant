import React, { useEffect, useState } from 'react';
import API from '../services/api';

const Menu = () => {
  const [menu, setMenu] = useState([]);

  useEffect(() => {
    API.get('/menu')
      .then((res) => setMenu(res.data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Menü</h1>
      <ul>
        {menu.map((item) => (
          <li key={item.id} className="border p-2 mb-2 rounded">
            <strong>{item.name}</strong> - {item.price} ₺
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Menu;
