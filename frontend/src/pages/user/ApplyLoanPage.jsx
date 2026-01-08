import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../../components/common/Navbar';
import Sidebar from '../../components/common/Sidebar';
import api from '../../services/api';

export default function ApplyLoanPage() {
  const navigate = useNavigate();
  const [loanTypes, setLoanTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  const [formData, setFormData] = useState({
    loan_type: 'personal',
    loan_provider: 'RISKOFF Bank',
    loan_amount: 100000,
    loan_tenure_months: 36,
    loan_purpose: ''
  });

  const providers = [
    'RISKOFF Bank',
    'ICICI Bank',
    'SBI',
    'HDFC Bank',
    'Axis Bank',
    'Kotak Mahindra Bank'
  ];

  useEffect(() => {
    fetchLoanTypes();
  }, []);

  const fetchLoanTypes = async () => {
    try {
      const response = await api.get('/loans/types/list');
      setLoanTypes(response. data. loan_types);
    } catch (error) {
      console.error('Error fetching loan types:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type } = e. target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.post('/loans/apply', formData);
      setResult(response.data);
    } catch (error) {
      console. error('Error applying for loan:', error);
      alert('Error submitting application');
    } finally {
      setLoading(false);
    }
  };

  const getTenureDisplay = (months) => {
    if (months < 12) return `${months} months`;
    return `${(months / 12).toFixed(1)} years`;
  };

  const selectedLoanType = loanTypes.find(lt => lt.id === formData.loan_type);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-dark-text mb-6">💰 Apply for Loan</h1>

          {result ? (
            <div className="max-w-2xl mx-auto">
              <div className={`rounded-xl p-8 text-center ${
                result.status === 'approved' ? 'bg-green-50 dark:bg-green-900/20 border-2 border-green-500' :
                result.status === 'rejected' ? 'bg-red-50 dark:bg-red-900/20 border-2 border-red-500' :
                'bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-500'
              }`}>
                <div className="text-5xl mb-4">
                  {result.status === 'approved' ? '✅' : 
                   result.status === 'rejected' ? '❌' : '⏳'}
                </div>
                <h2 className="text-2xl font-bold mb-2 dark:text-dark-text">
                  {result.status === 'approved' ? 'Loan Approved!' : 
                   result.status === 'rejected' ? 'Loan Rejected' : 'Under Review'}
                </h2>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  Application ID: #{result.loan_id}
                </p>
                
                <div className="grid grid-cols-2 gap-4 text-left mt-6 mb-6">
                  <div className="bg-white dark:bg-dark-card p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-dark-muted">Risk Score</p>
                    <p className="text-xl font-bold dark:text-dark-text">{result.risk_score}%</p>
                  </div>
                  <div className="bg-white dark:bg-dark-card p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-dark-muted">Risk Category</p>
                    <p className="text-xl font-bold dark:text-dark-text">{result.risk_category}</p>
                  </div>
                  <div className="bg-white dark:bg-dark-card p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-dark-muted">Monthly EMI</p>
                    <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                      ₹{result.monthly_emi?.toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-dark-card p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-dark-muted">Decision</p>
                    <p className="text-xl font-bold dark:text-dark-text">
                      {result.auto_decision ? 'Auto' : 'Manual Review'}
                    </p>
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">{result.recommendation}</p>

                <div className="flex gap-4 justify-center">
                  <button
                    onClick={() => navigate('/my-loans')}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700"
                  >
                    View My Loans
                  </button>
                  <button
                    onClick={() => {
                      setResult(null);
                      setFormData({
                        loan_type: 'personal',
                        loan_provider: 'RISKOFF Bank',
                        loan_amount: 100000,
                        loan_tenure_months: 36,
                        loan_purpose: ''
                      });
                    }}
                    className="bg-gray-200 dark:bg-dark-border text-gray-700 dark:text-dark-text px-6 py-2 rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-gray-600"
                  >
                    Apply for Another
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto bg-white dark:bg-dark-card rounded-xl shadow-sm p-8">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Loan Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-dark-muted mb-2">Loan Type</label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {loanTypes.map((type) => (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, loan_type: type.id }))}
                        className={`p-4 border-2 rounded-lg text-left transition ${
                          formData.loan_type === type.id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-dark-border hover:border-gray-300 dark:hover:border-gray-500'
                        }`}
                      >
                        <p className="font-semibold dark:text-dark-text">{type.name}</p>
                        <p className="text-xs text-gray-500 dark:text-dark-muted">{type.rate}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Loan Provider */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-dark-muted mb-1">Loan Provider</label>
                  <select
                    name="loan_provider"
                    value={formData.loan_provider}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border dark:border-dark-border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-dark-bg dark:text-dark-text"
                  >
                    {providers.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>

                {/* Loan Amount */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-dark-muted mb-1">
                    Loan Amount: ₹{formData.loan_amount.toLocaleString('en-IN')}
                  </label>
                  <input
                    type="range"
                    name="loan_amount"
                    value={formData.loan_amount}
                    onChange={handleChange}
                    min={selectedLoanType?.min || 10000}
                    max={selectedLoanType?.max || 1000000}
                    step={10000}
                    className="w-full accent-blue-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 dark:text-dark-muted">
                    <span>₹{(selectedLoanType?.min || 10000).toLocaleString('en-IN')}</span>
                    <span>₹{(selectedLoanType?.max || 1000000).toLocaleString('en-IN')}</span>
                  </div>
                </div>

                {/* Tenure */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-dark-muted mb-1">
                    Tenure: {getTenureDisplay(formData.loan_tenure_months)}
                  </label>
                  <input
                    type="range"
                    name="loan_tenure_months"
                    value={formData.loan_tenure_months}
                    onChange={handleChange}
                    min={6}
                    max={240}
                    step={6}
                    className="w-full accent-blue-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 dark:text-dark-muted">
                    <span>6 months</span>
                    <span>20 years</span>
                  </div>
                </div>

                {/* Purpose */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-dark-muted mb-1">Purpose (Optional)</label>
                  <textarea
                    name="loan_purpose"
                    value={formData.loan_purpose}
                    onChange={handleChange}
                    rows={3}
                    className="w-full px-4 py-2 border dark:border-dark-border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-dark-bg dark:text-dark-text"
                    placeholder="Brief description of loan purpose..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : '📤 Submit Application'}
                </button>
              </form>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}