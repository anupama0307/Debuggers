import React, { useState, useEffect } from 'react';
import Navbar from '../../components/common/Navbar';
import Sidebar from '../../components/common/Sidebar';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import api from '../../services/api';

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [profileRes, dashboardRes] = await Promise.all([
        api.get('/user/profile'),
        api.get('/user/dashboard')
      ]);
      setProfile(profileRes.data);
      setDashboard(dashboardRes.data);
      setFormData(profileRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    
    // For phone, only allow digits and limit to 10
    if (name === 'phone') {
      const cleaned = value.replace(/\D/g, '').slice(0, 10);
      setFormData(prev => ({ ...prev, [name]: cleaned }));
      return;
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (parseFloat(value) || 0) : value
    }));
  };

  const validateForm = () => {
    // Phone validation
    if (formData.phone && formData.phone.length !== 10) {
      setError('Phone number must be exactly 10 digits');
      return false;
    }
    
    // Annual income validation
    if (formData.annual_income && formData.annual_income < 50000) {
      setError('Annual income must be at least ₹50,000');
      return false;
    }
    
    // Monthly expenses validation
    if (formData.monthly_expenses && formData.monthly_expenses < 0) {
      setError('Monthly expenses cannot be negative');
      return false;
    }
    
    // Account balance validation
    if (formData.account_balance && formData.account_balance < 0) {
      setError('Account balance cannot be negative');
      return false;
    }
    
    return true;
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    
    // Validate before saving
    if (!validateForm()) {
      return;
    }
    
    setSaving(true);
    try {
      const response = await api.put('/user/profile', formData);
      setProfile(response.data.profile || formData);
      setEditing(false);
      setSuccess('Profile saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
      fetchData(); // Refresh both profile and dashboard
    } catch (error) {
      console.error('Error saving profile:', error);
      const detail = error.response?.data?.detail;
      // Handle Pydantic validation errors
      if (Array.isArray(detail)) {
        setError(detail.map(e => e.msg).join(', '));
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Failed to save profile');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-8">
            <LoadingSpinner text="Loading profile..." />
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-800">👤 My Profile</h1>
            {!editing? (
              <button
                onClick={() => setEditing(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700"
              >
                Edit Profile
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditing(false);
                    setFormData(profile);
                    setError('');
                  }}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 border border-red-200">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 text-green-600 p-3 rounded-lg mb-4 border border-green-200">
              {success}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Customer Score Card */}
            <div className="bg-white rounded-xl shadow-sm p-6 text-center">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Customer Score</h3>
              <div className="relative w-32 h-32 mx-auto mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="64" cy="64" r="56" fill="none" stroke="#E5E7EB" strokeWidth="12" />
                  <circle
                    cx="64" cy="64" r="56" fill="none"
                    stroke={dashboard?.customer_score >= 650 ? '#10B981' : dashboard?.customer_score >= 550 ? '#F59E0B' : '#EF4444'}
                    strokeWidth="12"
                    strokeDasharray={`${((dashboard?.customer_score || 0) / 900) * 351.86} 351.86`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-3xl font-bold">{dashboard?.customer_score || 0}</span>
                </div>
              </div>
              <p className="text-gray-500">out of 900</p>
              {!dashboard?.profile_completed && (
                <p className="text-blue-500 text-sm mt-2">💡 Add income details to improve score</p>
              )}
            </div>

            {/* Personal Info */}
            <div className="bg-white rounded-xl shadow-sm p-6 lg:col-span-2">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Personal Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Full Name</label>
                  {editing? (
                    <input
                      type="text"
                      name="full_name"
                      value={formData.full_name || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">{profile?.full_name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Email</label>
                  <p className="font-medium">{profile?.email}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Phone</label>
                  {editing? (
                    <div>
                      <input
                        type="tel"
                        name="phone"
                        value={formData.phone || ''}
                        onChange={handleChange}
                        maxLength={10}
                        placeholder="10 digit number"
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                          formData.phone && formData.phone.length !== 10 ? 'border-red-300' : ''
                        }`}
                      />
                      {formData.phone && formData.phone.length !== 10 && (
                        <p className="text-red-500 text-xs mt-1">Must be 10 digits ({formData.phone.length}/10)</p>
                      )}
                    </div>
                  ) : (
                    <p className="font-medium">{profile?.phone}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">City</label>
                  {editing? (
                    <input
                      type="text"
                      name="city"
                      value={formData.city || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">{profile?.city || 'N/A'}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Employment Info */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Employment</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Occupation</label>
                  {editing? (
                    <input
                      type="text"
                      name="occupation"
                      value={formData.occupation || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">{profile?.occupation || 'N/A'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Employer</label>
                  {editing?  (
                    <input
                      type="text"
                      name="employer_name"
                      value={formData.employer_name || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">{profile?.employer_name || 'N/A'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Years at Job</label>
                  {editing? (
                    <input
                      type="number"
                      name="employment_years"
                      value={formData.employment_years || 0}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">{profile?.employment_years || 0} years</p>
                  )}
                </div>
              </div>
            </div>

            {/* Financial Info */}
            <div className="bg-white rounded-xl shadow-sm p-6 lg:col-span-2">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Financial Information</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Annual Income (₹) *</label>
                  {editing? (
                    <div>
                      <input
                        type="number"
                        name="annual_income"
                        value={formData.annual_income || ''}
                        onChange={handleChange}
                        min={50000}
                        placeholder="Min ₹50,000"
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                          formData.annual_income && formData.annual_income < 50000 ? 'border-red-300' : ''
                        }`}
                      />
                      {formData.annual_income && formData.annual_income < 50000 && (
                        <p className="text-red-500 text-xs mt-1">Minimum ₹50,000 required</p>
                      )}
                    </div>
                  ) : (
                    <p className="font-medium text-green-600">
                      ₹{profile?.annual_income?.toLocaleString('en-IN') || 0}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Monthly Expenses (₹)</label>
                  {editing? (
                    <div>
                      <input
                        type="number"
                        name="monthly_expenses"
                        value={formData.monthly_expenses || ''}
                        onChange={handleChange}
                        min={0}
                        placeholder="Cannot be negative"
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                          formData.monthly_expenses < 0 ? 'border-red-300' : ''
                        }`}
                      />
                      {formData.monthly_expenses < 0 && (
                        <p className="text-red-500 text-xs mt-1">Cannot be negative</p>
                      )}
                    </div>
                  ) : (
                    <p className="font-medium text-red-600">
                      ₹{profile?.monthly_expenses?.toLocaleString('en-IN') || 0}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Account Balance (₹)</label>
                  {editing? (
                    <div>
                      <input
                        type="number"
                        name="account_balance"
                        value={formData.account_balance || ''}
                        onChange={handleChange}
                        min={0}
                        placeholder="Cannot be negative"
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                          formData.account_balance < 0 ? 'border-red-300' : ''
                        }`}
                      />
                      {formData.account_balance < 0 && (
                        <p className="text-red-500 text-xs mt-1">Cannot be negative</p>
                      )}
                    </div>
                  ) : (
                    <p className="font-medium text-blue-600">
                      ₹{profile?.account_balance?.toLocaleString('en-IN') || 0}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Mutual Funds (₹)</label>
                  {editing? (
                    <input
                      type="number"
                      name="mutual_funds"
                      value={formData.mutual_funds || 0}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">₹{profile?.mutual_funds?.toLocaleString('en-IN') || 0}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Stocks (₹)</label>
                  {editing? (
                    <input
                      type="number"
                      name="stocks"
                      value={formData.stocks || 0}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">₹{profile?.stocks?. toLocaleString('en-IN') || 0}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Fixed Deposits (₹)</label>
                  {editing? (
                    <input
                      type="number"
                      name="fixed_deposits"
                      value={formData.fixed_deposits || 0}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">₹{profile?.fixed_deposits?.toLocaleString('en-IN') || 0}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Existing Loans</label>
                  {editing? (
                    <input
                      type="number"
                      name="existing_loans"
                      value={formData.existing_loans || 0}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium">{profile?.existing_loans || 0}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">Existing Loan Amount (₹)</label>
                  {editing? (
                    <input
                      type="number"
                      name="existing_loan_amount"
                      value={formData.existing_loan_amount || 0}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="font-medium text-orange-600">
                      ₹{profile?.existing_loan_amount?.toLocaleString('en-IN') || 0}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}