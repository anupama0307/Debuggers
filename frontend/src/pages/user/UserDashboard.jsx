import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import Navbar from '../../components/common/Navbar';
import Sidebar from '../../components/common/Sidebar';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import api from '../../services/api';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export default function UserDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasFinancialData, setHasFinancialData] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await api.get('/user/dashboard');
      setData(response.data);
      setHasFinancialData(response.data?.has_financial_data || false);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 750) return 'text-green-600';
    if (score >= 650) return 'text-blue-600';
    if (score >= 550) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreGrade = (score) => {
    if (score >= 750) return 'Excellent';
    if (score >= 650) return 'Good';
    if (score >= 550) return 'Fair';
    if (score >= 400) return 'Poor';
    return 'Very Poor';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-8">
            <LoadingSpinner text="Loading dashboard..." />
          </main>
        </div>
      </div>
    );
  }

  const spendingData = data?.spending_breakdown?.map((item, index) => ({
    name: item.category,
    value: item.amount,
    color: COLORS[index % COLORS.length]
  })) || [];

  const incomeExpenseData = data?.income_vs_expense || [];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          {/* Welcome Banner for new users */}
          {!hasFinancialData && (
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 mb-6 text-white">
              <h2 className="text-xl font-bold mb-2">👋 Welcome to VisualPe!</h2>
              <p className="text-blue-100 mb-4">Get started by applying for your first loan. Your financial data will be displayed here once you submit a loan application.</p>
              <Link
                to="/apply-loan"
                className="inline-block bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold hover:bg-blue-50"
              >
                Apply for Your First Loan →
              </Link>
            </div>
          )}

          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-800">📊 VisualPe Dashboard</h1>
            <Link
              to="/apply-loan"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700"
            >
              + Apply for Loan
            </Link>
          </div>

          {/* Customer Score & Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {/* Customer Score */}
            <div className="bg-white rounded-xl shadow-sm p-6 col-span-1">
              <h3 className="text-sm text-gray-500 mb-2">Customer Score</h3>
              <div className="text-center">
                <p className={`text-4xl font-bold ${getScoreColor(data?.customer_score || 0)}`}>
                  {data?.customer_score || 0}
                </p>
                <p className="text-sm text-gray-500">out of 900</p>
                <p className={`font-semibold mt-1 ${getScoreColor(data?.customer_score || 0)}`}>
                  {getScoreGrade(data?.customer_score || 0)}
                </p>
              </div>
              {/* Score Bar */}
              <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${
                    data?.customer_score >= 750 ? 'bg-green-500' : 
                    data?.customer_score >= 650 ? 'bg-blue-500' :
                    data?.customer_score >= 550 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${((data?.customer_score || 0) / 900) * 100}%` }}
                />
              </div>
            </div>

            {/* Monthly Income */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-sm text-gray-500 mb-2">Monthly Income</h3>
              <p className="text-2xl font-bold text-green-600">
                ₹{data?.monthly_income?.toLocaleString('en-IN') || 0}
              </p>
            </div>

            {/* Monthly Expenses */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-sm text-gray-500 mb-2">Monthly Expenses</h3>
              <p className="text-2xl font-bold text-red-600">
                ₹{data?.monthly_expenses?. toLocaleString('en-IN') || 0}
              </p>
              {data?.expense_mismatch && (
                <p className="text-xs text-red-500 mt-1">
                  ⚠️ Mismatch: {data?.expense_mismatch_percent}%
                </p>
              )}
            </div>

            {/* Total Assets */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-sm text-gray-500 mb-2">Total Assets</h3>
              <p className="text-2xl font-bold text-blue-600">
                ₹{data?.total_assets?. toLocaleString('en-IN') || 0}
              </p>
            </div>
          </div>

          {/* Loan Summary Alert */}
          {data?.loan_summary?. pending > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
              <p className="text-yellow-800">
                📋 You have <strong>{data.loan_summary.pending}</strong> pending loan application(s).{' '}
                <Link to="/my-loans" className="text-yellow-700 underline">View status</Link>
              </p>
            </div>
          )}

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Spending Breakdown */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">💰 Spending Breakdown</h3>
              {spendingData. length > 0 ?  (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={spendingData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {spendingData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  Upload bank statement to see spending breakdown
                </div>
              )}
              <div className="flex flex-wrap justify-center gap-3 mt-4">
                {spendingData.map((item, index) => (
                  <div key={index} className="flex items-center text-sm">
                    <div className="w-3 h-3 rounded-full mr-1" style={{ backgroundColor:  item.color }} />
                    <span className="capitalize">{item.name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Income vs Expense Trend */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">📈 Income vs Expense</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={incomeExpenseData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                  <Bar dataKey="income" fill="#10B981" name="Income" />
                  <Bar dataKey="expenses" fill="#EF4444" name="Expenses" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Investments Breakdown */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">📊 Investment Portfolio</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-500">Account Balance</p>
                <p className="text-lg font-bold text-blue-600">
                  ₹{data?.account_balance?.toLocaleString('en-IN') || 0}
                </p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-500">Mutual Funds</p>
                <p className="text-lg font-bold text-green-600">
                  ₹{data?.investments?.mutual_funds?.toLocaleString('en-IN') || 0}
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-gray-500">Stocks</p>
                <p className="text-lg font-bold text-purple-600">
                  ₹{data?.investments?.stocks?. toLocaleString('en-IN') || 0}
                </p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-sm text-gray-500">Fixed Deposits</p>
                <p className="text-lg font-bold text-yellow-600">
                  ₹{data?.investments?.fixed_deposits?.toLocaleString('en-IN') || 0}
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Other</p>
                <p className="text-lg font-bold text-gray-600">
                  ₹{data?.investments?.other?. toLocaleString('en-IN') || 0}
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}