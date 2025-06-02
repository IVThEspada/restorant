// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ManagerDashboard from './pages/ManagerDashboard';
import ProtectedRoute from './auth/ProtectedRoute';

function App() {
  return (
    <Router>
      <Routes>
        <Route
          path="/manager-dashboard"
          element={
            <ProtectedRoute roles={['MANAGER']}>
              <ManagerDashboard />
            </ProtectedRoute>
          }
        />
        {/* Diğer sayfalar varsa buraya eklenebilir */}
      </Routes>
    </Router>
  );
}

export default App;
