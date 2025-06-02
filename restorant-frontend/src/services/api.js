import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
});

API.interceptors.request.use((req) => {
  const token = localStorage.getItem('token');
  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
  }
  return req;
});

// Login fonksiyonunu ayrı export et
export const loginUser = async (username, password) => {
  const response = await API.post('/auth/login', { username, password });
  return response.data;
};

export default API;
