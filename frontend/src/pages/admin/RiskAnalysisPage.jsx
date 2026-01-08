import React, { useState } from 'react';
import Navbar from '../../components/common/Navbar';
import Sidebar from '../../components/common/Sidebar';
import api from '../../services/api';

export default function RiskAnalysisPage() {
  const [formData, setFormData] = useState({
    age: 30,
    annual_income: 600000,
    employment_years: 4,
    existing_loan_amount: 50000,
    monthly_expenses: 25000,
    loan_amount_requested: 200000,
    loan_tenure_months: 36,
    customer_score: 650,
    has_expense_mismatch: false
  });
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ?  checked : type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.post('/admin/risk-analysis', formData);
      setResult(response.data);
    } catch (error) {
      console.error('Error analyzing risk:', error);
      alert('Failed to analyze risk. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getTenureDisplay = (months) => {
    if (months < 12) return `${months} months`;
    return `${(months / 12).toFixed(1)} years`;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">🎯 Risk Analysis Tool</h1>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Form */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Customer Details</h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Age</label>
                    <input
                      type="number"
                      name="age"
                      value={formData.age}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Annual Income (₹)</label>
                    <input
                      type="number"
                      name="annual_income"
                      value={formData.annual_income}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Employment Years</label>
                    <input
                      type="number"
                      name="employment_years"
                      value={formData.employment_years}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Monthly Expenses (₹)</label>
                    <input
                      type="number"
                      name="monthly_expenses"
                      value={formData.monthly_expenses}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Existing Loan Amount (₹)</label>
                    <input
                      type="number"
                      name="existing_loan_amount"
                      value={formData.existing_loan_amount}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Customer Score (0-900)</label>
                    <input
                      type="number"
                      name="customer_score"
                      value={formData.customer_score}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                      min="0"
                      max="900"
                    />
                  </div>
                </div>

                <hr className="my-4 dark:border-slate-600" />
                <h3 className="font-semibold text-gray-800 dark:text-white">Loan Details</h3>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">Loan Amount (₹)</label>
                    <input
                      type="number"
                      name="loan_amount_requested"
                      value={formData.loan_amount_requested}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">
                      Tenure: {getTenureDisplay(formData.loan_tenure_months)}
                    </label>
                    <input
                      type="range"
                      name="loan_tenure_months"
                      value={formData.loan_tenure_months}
                      onChange={handleChange}
                      className="w-full accent-blue-600"
                      min="6"
                      max="240"
                      step="6"
                    />
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="has_expense_mismatch"
                    checked={formData.has_expense_mismatch}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700 dark:text-gray-400">Has Expense Mismatch (Fraud Flag)</label>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Analyzing...' : '🎯 Analyze Risk'}
                </button>
              </form>
            </div>

            {/* Result */}
            <div>
              {result ? (
                <div className="space-y-4">
                  {/* Decision Card */}
                  <div className={`rounded-xl p-6 ${
                    result.decision === 'AUTO_APPROVE' ? 'bg-green-50 dark:bg-green-900/20 border-2 border-green-500' :
                    result.decision === 'MANUAL_REVIEW' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-500' :
                    'bg-red-50 dark:bg-red-900/20 border-2 border-red-500'
                  }`}>
                    <div className="text-center">
                      <div className="text-4xl mb-2">
                        {result.decision === 'AUTO_APPROVE' ? '✅' : 
                         result.decision === 'MANUAL_REVIEW' ? '⚠️' : '❌'}
                      </div>
                      <h2 className="text-2xl font-bold dark:text-white">
                        {result.decision === 'AUTO_APPROVE' ? 'Auto Approve' : 
                         result.decision === 'MANUAL_REVIEW' ? 'Manual Review' : 'Auto Reject'}
                      </h2>
                      <div className="mt-4">
                        <p className="text-sm dark:text-gray-400">Risk Score</p>
                        <p className="text-3xl font-bold dark:text-white">{result.risk_percentage}%</p>
                        <p className="text-sm font-semibold mt-1 dark:text-gray-400">{result.risk_category} RISK</p>
                      </div>
                    </div>
                  </div>

                  {/* EMI Info */}
                  <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6">
                    <h3 className="font-semibold text-gray-800 dark:text-white mb-4">📊 EMI Analysis</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Monthly EMI</p>
                        <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                          ₹{result.monthly_emi?.toLocaleString('en-IN')}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">EMI to Income</p>
                        <p className="text-xl font-bold dark:text-white">{result.emi_to_income_ratio}%</p>
                      </div>
                    </div>
                  </div>

                  {/* Max Loan */}
                  <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6">
                    <h3 className="font-semibold text-gray-800 dark:text-white mb-2">💰 Max Recommended Loan</h3>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      ₹{result.max_recommended_loan?.toLocaleString('en-IN')}
                    </p>
                  </div>

                  {/* Risk Factors */}
                  <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6">
                    <h3 className="font-semibold text-gray-800 dark:text-white mb-3">🔍 Risk Factors</h3>
                    <ul className="space-y-2">
                      {result.risk_factors?.map((factor, index) => (
                        <li key={index} className="flex items-start text-sm dark:text-gray-400">
                          <span className="text-red-500 mr-2">•</span>
                          {factor}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Recommendation */}
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-6 border border-yellow-200 dark:border-yellow-800">
                    <h3 className="font-semibold text-yellow-800 dark:text-yellow-400 mb-2">📋 Recommendation</h3>
                    <p className="text-yellow-900 dark:text-yellow-300">{result.recommendation}</p>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 dark:bg-slate-800 rounded-xl border-2 border-dashed border-gray-300 dark:border-slate-600 p-12 text-center">
                  <div className="text-6xl mb-4">📊</div>
                  <h3 className="text-lg font-semibold text-gray-700 dark:text-white">Risk Analysis Result</h3>
                  <p className="text-gray-500 dark:text-gray-400 mt-2">Fill the form and click "Analyze Risk"</p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}