import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../../components/common/Navbar';
import Sidebar from '../../components/common/Sidebar';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import api from '../../services/api';

export default function LoanApplicationsPage() {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchLoans();
  }, []);

  const fetchLoans = async () => {
    try {
      setError('');
      const response = await api.get('/admin/loans');
      console.log('Admin loans response:', response.data);
      // Backend returns { loans: [...] } object
      const loansData = response.data?.loans || response.data || [];
      setLoans(Array.isArray(loansData) ? loansData : []);
    } catch (error) {
      console.error('Error fetching loans:', error);
      const detail = error.response?.data?.detail || error.response?.data?.message;
      if (error.response?.status === 403) {
        setError('Access denied. Admin privileges required.');
      } else if (error.response?.status === 401) {
        setError('Session expired. Please log in again.');
      } else {
        setError(typeof detail === 'string' ? detail : 'Failed to load loans');
      }
      setLoans([]);
    } finally {
      setLoading(false);
    }
  };

  // Filter loans based on selected filter
  const filteredLoans = filter === 'all' 
    ? loans 
    : loans.filter(loan => (loan.status || 'pending').toLowerCase() === filter.toLowerCase());

  const handleStatusUpdate = async (loanId, newStatus, remarks = '') => {
    try {
      await api.patch(`/admin/loans/${loanId}/status`, {
        status: newStatus.toUpperCase(),
        remarks: remarks
      });
      fetchLoans();
    } catch (error) {
      console.error('Error updating status:', error);
      setError('Failed to update loan status');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-100 text-yellow-700',
      approved:  'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700'
    };
    return badges[status] || 'bg-gray-100 text-gray-700';
  };

  const getRiskBadge = (category) => {
    const badges = {
      LOW: 'bg-green-100 text-green-700',
      MEDIUM:  'bg-yellow-100 text-yellow-700',
      HIGH: 'bg-red-100 text-red-700'
    };
    return badges[category] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          {error && (
            <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg">
              {error}
            </div>
          )}
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Loan Applications</h1>
            
            {/* Filter Tabs */}
            <div className="flex space-x-2">
              {['all', 'pending', 'approved', 'rejected'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    filter === f
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-slate-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700'
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <LoadingSpinner text="Loading applications..." />
          ) : filteredLoans.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              No {filter === 'all' ? '' : filter} loan applications found
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm overflow-hidden">
              <table className="w-full">
                <thead className={`${
                  filter === 'pending' ? 'bg-yellow-50 dark:bg-yellow-900/20' :
                  filter === 'approved' ? 'bg-green-50 dark:bg-green-900/20' :
                  filter === 'rejected' ? 'bg-red-50 dark:bg-red-900/20' :
                  'bg-gray-50 dark:bg-slate-700'
                }`}>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Customer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Purpose</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Risk</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-slate-600">
                  {filteredLoans.map((loan) => (
                    <tr key={loan.id} className="hover:bg-gray-50 dark:hover:bg-slate-700">
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">#{loan.id}</td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">{loan.user_name || loan.full_name || 'N/A'}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">{loan.user_email || loan.email || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-white capitalize">{loan.purpose || 'General'}</td>
                      <td className="px-6 py-4 text-sm font-semibold text-gray-900 dark:text-white">
                        ₹{(loan.amount || loan.loan_amount)?.toLocaleString('en-IN')}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskBadge(loan.risk_category)}`}>
                          {loan.risk_category || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge((loan.status || 'pending').toLowerCase())}`}>
                          {(loan.status || 'PENDING').toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {(loan.status?.toUpperCase() === 'PENDING' || !loan.status) ? (
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleStatusUpdate(loan.id, 'APPROVED', 'Approved by admin')}
                              className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 font-medium"
                            >
                              ✓ Approve
                            </button>
                            <button
                              onClick={() => handleStatusUpdate(loan.id, 'REJECTED', 'Rejected by admin')}
                              className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200 font-medium"
                            >
                              ✗ Reject
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => navigate(`/admin/loans/${loan.id}`)}
                            className="px-3 py-1 bg-gray-100 dark:bg-slate-600 text-gray-700 dark:text-gray-200 rounded text-sm hover:bg-gray-200"
                          >
                            View Details
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}