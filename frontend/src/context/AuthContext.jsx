import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, user_id, email: userEmail, full_name } = response.data;
    
    // Set token first so we can fetch profile
    localStorage.setItem('token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    // Fetch actual role from profile
    let role = 'user';
    try {
      const profileResponse = await api.get('/user/profile');
      role = profileResponse.data?.role || 'user';
    } catch (err) {
      console.error('Error fetching profile role:', err);
    }
    
    const userData = {
      id: user_id,
      email: userEmail,
      full_name: full_name,
      role: role
    };
    
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const verifyOTP = async (email, otp) => {
    // OTP not used - login handles everything directly
    return user;
  };

  const register = async (data) => {
    const response = await api.post('/auth/signup', data);
    const { access_token, user_id, email: userEmail, full_name, message } = response.data;
    
    // If email confirmation is required (no token returned)
    if (!access_token) {
      return { requiresEmailConfirmation: true, message };
    }
    
    const userData = {
      id: user_id,
      email: userEmail,
      full_name: full_name,
      role: 'user'
    };
    
    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    setUser(userData);
    return userData;
  };

  const verifyRegisterOTP = async (email, otp) => {
    // OTP not used - register handles everything directly
    return user;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, verifyOTP, register, verifyRegisterOTP, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);