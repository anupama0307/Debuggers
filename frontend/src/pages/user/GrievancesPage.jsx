import React, { useState, useEffect } from 'react';
import Navbar from '../../components/common/Navbar';
import Sidebar from '../../components/common/Sidebar';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import api from '../../services/api';

export default function UserGrievancesPage() {
  const [grievances, setGrievances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    grievance_type: 'other'
  });

  useEffect(() => {
    fetchGrievances();
  }, []);

  const fetchGrievances = async () => {
    try {
      const response = await api.get('/grievances/my-grievances');
      setGrievances(response.data);
    } catch (error) {
      console.error('Error fetching grievances:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await api.post('/grievances/submit', formData);
      setShowForm(false);
      setFormData({ subject: '', description:  '', grievance_type: 'other' });
      fetchGrievances();
    } catch (error) {
      console.error('Error submitting grievance:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      open: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
      in_progress: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
      resolved: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
    };
    return badges[status] || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">💬 My Grievances</h1>
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700"
            >
              {showForm ? 'Cancel' : '+ New Grievance'}
            </button>
          </div>

          {/* New Grievance Form */}
          {showForm && (
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Submit New Grievance</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Type</label>
                  <select
                    value={formData.grievance_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, grievance_type: e.target.value }))}
                    className="w-full px-4 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                  >
                    <option value="rejection_query">Loan Rejection Query</option>
                    <option value="delay">Processing Delay</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Subject</label>
                  <input
                    type="text"
                    value={formData.subject}
                    onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                    className="w-full px-4 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    placeholder="Brief subject of your grievance"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                    className="w-full px-4 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    placeholder="Describe your issue in detail..."
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Grievance'}
                </button>
              </form>
            </div>
          )}

          {/* Grievances List */}
          {loading ? (
            <LoadingSpinner text="Loading grievances..." />
          ) : grievances.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-12 text-center">
              <div className="text-6xl mb-4">📭</div>
              <h3 className="text-xl font-semibold text-gray-700 dark:text-white mb-2">No Grievances</h3>
              <p className="text-gray-500 dark:text-gray-400">You haven't submitted any grievances yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {grievances.map((g) => (
                <div key={g.id} className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-800 dark:text-white">{g.subject}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(g.created_at).toLocaleDateString()} • {g.grievance_type}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(g.status)}`}>
                      {g.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>

                  <p className="text-gray-600 dark:text-gray-300 mb-4">{g.description}</p>

                  {g.admin_response && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-l-4 border-blue-500">
                      <p className="text-sm font-medium text-blue-700 dark:text-blue-400 mb-1">Admin Response:</p>
                      <p className="text-sm text-blue-800 dark:text-blue-300 whitespace-pre-wrap">{g.admin_response}</p>
                    </div>
                  )}

                  {g.status === 'resolved' && g.resolved_at && (
                    <p className="text-sm text-green-600 mt-2">
                      ✓ Resolved on {new Date(g.resolved_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}