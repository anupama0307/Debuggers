import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/common/Navbar";
import Sidebar from "../../components/common/Sidebar";
import api from "../../services/api";

export default function ApplyLoanPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // MATCH BACKEND SCHEMA: { amount, tenure_months, monthly_income, monthly_expenses, purpose }
  const [formData, setFormData] = useState({
    amount: 100000,
    tenure_months: 36,
    monthly_income: 50000,
    monthly_expenses: 20000,
    purpose: "",
  });

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      // Ensure numbers are sent as numbers, not strings
      [name]:
        type === "number" || type === "range"
          ? (name === "tenure_months"
              ? parseInt(value, 10)
              : parseFloat(value)) || 0
          : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // Send exactly what backend expects
      const payload = {
        amount: parseFloat(formData.amount),
        tenure_months: parseInt(formData.tenure_months, 10),
        monthly_income: parseFloat(formData.monthly_income),
        monthly_expenses: parseFloat(formData.monthly_expenses),
        purpose: formData.purpose || "",
      };

      const response = await api.post("/loans/apply", payload);
      setResult(response.data);
    } catch (err) {
      console.error('Error applying for loan:', err);
      const detail = err.response?.data?.detail;
      // Handle FastAPI validation errors (array of objects) or string errors
      if (Array.isArray(detail)) {
        setError(detail.map(e => e.msg || JSON.stringify(e)).join(', '));
      } else if (typeof detail === 'object' && detail !== null) {
        setError(detail.msg || JSON.stringify(detail));
      } else {
        setError(detail || 'Error submitting application');
      }
    } finally {
      setLoading(false);
    }
  };

  // Calculate estimated EMI for display
  const calculateEMI = () => {
    const principal = formData.amount;
    const months = formData.tenure_months;
    const rate = 0.12 / 12; // Assuming 12% annual rate
    if (months === 0) return 0;
    const emi =
      (principal * rate * Math.pow(1 + rate, months)) /
      (Math.pow(1 + rate, months) - 1);
    return Math.round(emi);
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
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">
            💰 Apply for Loan
          </h1>

          {result ? (
            <div className="max-w-2xl mx-auto">
              <div
                className={`rounded-xl p-8 text-center ${
                  result.status === "APPROVED"
                    ? "bg-green-50 dark:bg-green-900/20 border-2 border-green-500"
                    : result.status === "REJECTED"
                    ? "bg-red-50 dark:bg-red-900/20 border-2 border-red-500"
                    : "bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-500"
                }`}
              >
                <div className="text-5xl mb-4">
                  {result.status === "APPROVED"
                    ? "✅"
                    : result.status === "REJECTED"
                    ? "❌"
                    : "⏳"}
                </div>
                <h2 className="text-2xl font-bold mb-2 dark:text-white">
                  {result.status === "APPROVED"
                    ? "Loan Approved!"
                    : result.status === "REJECTED"
                    ? "Loan Rejected"
                    : "Under Review"}
                </h2>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  Application ID: #{result.loan_id || result.id}
                </p>

                <div className="grid grid-cols-2 gap-4 text-left mt-6 mb-6">
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Risk Score</p>
                    <p className="text-xl font-bold dark:text-white">{Math.round(result.risk_score || 0)}%</p>
                  </div>
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Max Approved Amount</p>
                    <p className="text-xl font-bold text-green-600 dark:text-green-400">
                      {result.max_approved_amount ? `₹${result.max_approved_amount.toLocaleString('en-IN')}` : 'N/A'}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Monthly EMI
                    </p>
                    <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                      ₹{Math.round(result.emi || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Application ID</p>
                    <p className="text-xl font-bold dark:text-white">#{result.id}</p>
                  </div>
                </div>

                {result.ai_explanation && (
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-lg text-left mb-6">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">AI Explanation</p>
                    <p className="text-gray-700 dark:text-gray-300">{result.ai_explanation}</p>
                  </div>
                )}

                {result.risk_reason && (
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-lg text-left mb-6 border-l-4 border-orange-500">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">📊 Detailed Risk Assessment</p>
                    <ul className="text-gray-700 dark:text-gray-300 space-y-1">
                      {result.risk_reason.split(', ').map((reason, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-orange-500">•</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-4 justify-center">
                  <button
                    onClick={() => navigate("/my-loans")}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700"
                  >
                    View My Loans
                  </button>
                  <button
                    onClick={() => {
                      setResult(null);
                      setError("");
                      setFormData({
                        amount: 100000,
                        tenure_months: 36,
                        monthly_income: 50000,
                        monthly_expenses: 20000,
                        purpose: "",
                      });
                    }}
                    className="bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-slate-600"
                  >
                    Apply for Another
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto bg-white dark:bg-slate-800 rounded-xl shadow-sm p-8">
              {error && (
                <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-red-700 dark:text-red-300">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Loan Amount */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Loan Amount: ₹{formData.amount.toLocaleString("en-IN")}
                  </label>
                  <input
                    type="range"
                    name="amount"
                    value={formData.amount}
                    onChange={handleChange}
                    min={10000}
                    max={5000000}
                    step={10000}
                    className="w-full accent-blue-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                    <span>₹10,000</span>
                    <span>₹50,00,000</span>
                  </div>
                </div>

                {/* Tenure */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Loan Tenure: {getTenureDisplay(formData.tenure_months)}
                  </label>
                  <input
                    type="range"
                    name="tenure_months"
                    value={formData.tenure_months}
                    onChange={handleChange}
                    min={6}
                    max={240}
                    step={6}
                    className="w-full accent-blue-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                    <span>6 months</span>
                    <span>20 years</span>
                  </div>
                </div>

                {/* Monthly Income */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Monthly Income (₹)
                  </label>
                  <input
                    type="number"
                    name="monthly_income"
                    value={formData.monthly_income}
                    onChange={handleChange}
                    min={0}
                    className="w-full px-4 py-3 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    placeholder="Enter your monthly income"
                    required
                  />
                </div>

                {/* Monthly Expenses */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Monthly Expenses (₹)
                  </label>
                  <input
                    type="number"
                    name="monthly_expenses"
                    value={formData.monthly_expenses}
                    onChange={handleChange}
                    min={0}
                    className="w-full px-4 py-3 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    placeholder="Enter your monthly expenses"
                    required
                  />
                </div>

                {/* Purpose */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Loan Purpose (Optional)
                  </label>
                  <textarea
                    name="purpose"
                    value={formData.purpose}
                    onChange={handleChange}
                    rows={3}
                    className="w-full px-4 py-3 border dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-900 dark:text-white"
                    placeholder="Brief description of why you need this loan..."
                  />
                </div>

                {/* EMI Preview */}
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="flex justify-between items-center">
                    <span className="text-blue-700 dark:text-blue-300 font-medium">
                      Estimated Monthly EMI
                    </span>
                    <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      ₹{calculateEMI().toLocaleString("en-IN")}
                    </span>
                  </div>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    *Approximate calculation at 12% annual interest rate
                  </p>
                </div>

                {/* Disposable Income Warning */}
                {formData.monthly_income - formData.monthly_expenses <
                  calculateEMI() && (
                  <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                    <p className="text-yellow-700 dark:text-yellow-300 text-sm">
                      ⚠️ Your disposable income (₹
                      {(
                        formData.monthly_income - formData.monthly_expenses
                      ).toLocaleString("en-IN")}
                      ) may be insufficient for the estimated EMI. This could
                      affect your approval.
                    </p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Submitting..." : "📤 Submit Application"}
                </button>
              </form>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
