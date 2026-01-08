import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: ''
  });

  const { register } = useAuth();
  const navigate = useNavigate();

  // Field Validation
  const validateField = (name, value) => {
    const nameRegex = /^[a-zA-Z\s]*$/;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    switch (name) {
      case 'full_name':
        if (!value) return "Full Name is required";
        if (!nameRegex.test(value)) return "Name cannot contain numbers or symbols";
        if (value.length < 2) return "Name must be at least 2 characters";
        break;
      case 'email':
        if (!value) return "Email is required";
        if (!emailRegex.test(value)) return "Invalid email address";
        break;
      case 'password':
        if (!value) return "Password is required";
        if (value.length < 8) return "Password must be at least 8 characters";
        break;
      case 'confirmPassword':
        if (!value) return "Please confirm your password";
        if (value !== formData.password) return "Passwords do not match";
        break;
      case 'phone':
        if (!value) return "Phone number is required";
        if (!/^\d{10,15}$/.test(value)) return "Phone must be 10-15 digits";
        break;
      default:
        break;
    }
    return "";
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Only allow digits for phone
    if (name === 'phone' && !/^\d*$/.test(value)) return;

    setFormData(prev => ({ ...prev, [name]: value }));
    
    const errorMsg = validateField(name, value);
    setValidationErrors(prev => ({ ...prev, [name]: errorMsg }));
  };

  const validateForm = () => {
    const errors = {};
    let isValid = true;
    
    ['full_name', 'email', 'password', 'confirmPassword', 'phone'].forEach(field => {
      const error = validateField(field, formData[field]);
      if (error) {
        errors[field] = error;
        isValid = false;
      }
    });
    
    setValidationErrors(errors);
    return isValid;
  };

  // Helper to extract error message from API response
  const getErrorMessage = (err) => {
    const detail = err.response?.data?.detail;
    if (!detail) return 'Registration failed';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
    }
    if (typeof detail === 'object' && detail.msg) return detail.msg;
    return 'Registration failed';
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError('');
    
    try {
      const result = await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        phone: formData.phone
      });
      
      if (result.requiresEmailConfirmation) {
        setSuccess(true);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const getInputClass = (fieldName) => {
    return `w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
      validationErrors[fieldName] 
        ? 'border-red-500 bg-red-50' 
        : 'border-gray-300'
    }`;
  };

  // Success state - email confirmation required
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 text-center">
          <div className="text-6xl mb-4">📧</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Check Your Email</h1>
          <p className="text-gray-600 mb-4">
            We've sent a confirmation link to<br/>
            <span className="font-semibold text-blue-600">{formData.email}</span>
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Please click the link in the email to activate your account.
          </p>
          <Link
            to="/login"
            className="inline-block w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">🛡️ RISKON</h1>
          <p className="text-gray-500 mt-2">Create your account</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4">
          {/* Full Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              className={getInputClass('full_name')}
              placeholder="John Doe"
              required
            />
            {validationErrors.full_name && (
              <p className="text-red-500 text-xs mt-1">{validationErrors.full_name}</p>
            )}
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={getInputClass('email')}
              placeholder="you@example.com"
              required
            />
            {validationErrors.email && (
              <p className="text-red-500 text-xs mt-1">{validationErrors.email}</p>
            )}
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className={getInputClass('phone')}
              placeholder="1234567890"
              maxLength="15"
              required
            />
            {validationErrors.phone && (
              <p className="text-red-500 text-xs mt-1">{validationErrors.phone}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={getInputClass('password')}
              placeholder="••••••••"
              required
            />
            {validationErrors.password && (
              <p className="text-red-500 text-xs mt-1">{validationErrors.password}</p>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              className={getInputClass('confirmPassword')}
              placeholder="••••••••"
              required
            />
            {validationErrors.confirmPassword && (
              <p className="text-red-500 text-xs mt-1">{validationErrors.confirmPassword}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-600 font-semibold hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}