import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function RegisterPage() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(''); // General API errors
  const [validationErrors, setValidationErrors] = useState({}); // Field-specific errors
  const [otp, setOtp] = useState('');
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    date_of_birth: '',
    gender: 'male',
    address: '',
    city: '',
    state: '',
    pincode: '',
    occupation: '',
    employer_name: '',
    employment_years: 0,
    annual_income: 0,
    monthly_expenses: 0,
    account_balance: 0,
    mutual_funds: 0,
    stocks: 0,
    fixed_deposits: 0,
    existing_loans: 0,
    existing_loan_amount: 0
  });

  const { register, verifyRegisterOTP } = useAuth();
  const navigate = useNavigate();

  // --- VALIDATION LOGIC ---

  const validateStep1 = () => {
    const errors = {};
    const nameRegex = /^[a-zA-Z\s]+$/;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneRegex = /^[0-9]{10}$/;
    const pincodeRegex = /^[0-9]{6}$/;

    // Full Name
    if (!formData.full_name.trim()) errors.full_name = "Full Name is required";
    else if (!nameRegex.test(formData.full_name)) errors.full_name = "Name cannot contain numbers or symbols";

    // Email
    if (!emailRegex.test(formData.email)) errors.email = "Invalid email format";

    // Password
    if (formData.password.length < 6) errors.password = "Password must be at least 6 characters";

    // Phone
    if (!phoneRegex.test(formData.phone)) errors.phone = "Phone must be exactly 10 digits";

    // Age Check (18-100)
    if (!formData.date_of_birth) errors.date_of_birth = "Date of Birth is required";
    else {
      const birthDate = new Date(formData.date_of_birth);
      const today = new Date();
      let age = today.getFullYear() - birthDate.getFullYear();
      const m = today.getMonth() - birthDate.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
      
      if (age < 18) errors.date_of_birth = "You must be at least 18 years old";
      if (age > 100) errors.date_of_birth = "Please enter a valid date";
    }

    // Address Fields
    if (!formData.address.trim()) errors.address = "Address is required";
    
    if (!formData.city.trim()) errors.city = "City is required";
    else if (!nameRegex.test(formData.city)) errors.city = "City should contain only letters";

    if (!formData.state.trim()) errors.state = "State is required";
    else if (!nameRegex.test(formData.state)) errors.state = "State should contain only letters";

    if (!formData.pincode) errors.pincode = "Pincode is required";
    else if (!pincodeRegex.test(formData.pincode)) errors.pincode = "Invalid Pincode (6 digits)";

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateStep2 = () => {
    const errors = {};
    const textOnlyRegex = /^[a-zA-Z\s]+$/;

    // Occupation & Employer
    if (!formData.occupation.trim()) errors.occupation = "Occupation is required";
    else if (!textOnlyRegex.test(formData.occupation)) errors.occupation = "Invalid characters in occupation";

    if (!formData.employer_name.trim()) errors.employer_name = "Employer name is required";

    // Years at Job
    if (formData.employment_years < 0) errors.employment_years = "Years cannot be negative";
    if (formData.employment_years > 60) errors.employment_years = "Please enter a valid duration";

    // Income & Expenses Logic
    if (!formData.annual_income || formData.annual_income <= 0) {
        errors.annual_income = "Valid annual income is required";
    }
    
    if (formData.monthly_expenses < 0) {
        errors.monthly_expenses = "Expenses cannot be negative";
    }

    // Logic: Expenses vs Income check
    const monthlyIncome = formData.annual_income / 12;
    if (formData.monthly_expenses > monthlyIncome) {
        errors.monthly_expenses = "Expenses cannot exceed monthly income";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateStep3 = () => {
    const errors = {};
    
    // Financial assets cannot be negative
    if (formData.account_balance < 0) errors.account_balance = "Cannot be negative";
    if (formData.mutual_funds < 0) errors.mutual_funds = "Cannot be negative";
    if (formData.stocks < 0) errors.stocks = "Cannot be negative";
    if (formData.fixed_deposits < 0) errors.fixed_deposits = "Cannot be negative";
    
    // Loan Logic
    if (formData.existing_loans < 0) errors.existing_loans = "Cannot be negative";
    
    // If user has loans, amount must be > 0
    if (formData.existing_loans > 0 && formData.existing_loan_amount <= 0) {
        errors.existing_loan_amount = "Please specify amount for existing loans";
    }

    // If user has no loans, amount should be 0 (auto-correct or warn)
    if (formData.existing_loans === 0 && formData.existing_loan_amount > 0) {
        errors.existing_loans = "You have an amount but 0 loans count";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // --- HANDLERS ---

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    
    // Clear specific error when user types
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }

    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value
    }));
  };

  const nextStep = () => {
    let isValid = false;
    if (step === 1) isValid = validateStep1();
    if (step === 2) isValid = validateStep2();
    
    if (isValid) setStep(prev => prev + 1);
  };

  const prevStep = () => {
    setValidationErrors({}); // Clear errors when going back
    setStep(prev => prev - 1);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!validateStep3()) return; // Validate final step

    setLoading(true);
    setError('');
    
    try {
      await register(formData);
      setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await verifyRegisterOTP(formData.email, otp);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  // Helper for conditional styling
  const getInputClass = (fieldName) => {
    return `w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 transition-colors ${
      validationErrors[fieldName] 
        ? 'border-red-500 bg-red-50 focus:border-red-500 focus:ring-red-200' 
        : 'border-gray-300'
    }`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">🛡️ RISKON + VisualPe</h1>
          <p className="text-gray-500 mt-2">Create your account</p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                step >= s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                {s}
              </div>
              {s < 4 && <div className={`w-12 h-1 ${step > s ? 'bg-blue-600' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>

        {/* Global Error Message */}
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm border border-red-200 text-center font-medium">
            {error}
          </div>
        )}

        {/* Step 1: Personal Information */}
        {step === 1 && (
          <div className="space-y-4 animate-fadeIn">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Personal Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className={getInputClass('full_name')}
                  placeholder="John Doe"
                />
                {validationErrors.full_name && <p className="text-red-500 text-xs mt-1">{validationErrors.full_name}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={getInputClass('email')}
                  placeholder="john@example.com"
                />
                {validationErrors.email && <p className="text-red-500 text-xs mt-1">{validationErrors.email}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={getInputClass('password')}
                  placeholder="••••••••"
                />
                {validationErrors.password && <p className="text-red-500 text-xs mt-1">{validationErrors.password}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className={getInputClass('phone')}
                  placeholder="9876543210"
                  maxLength="10"
                />
                {validationErrors.phone && <p className="text-red-500 text-xs mt-1">{validationErrors.phone}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth *</label>
                <input
                  type="date"
                  name="date_of_birth"
                  value={formData.date_of_birth}
                  onChange={handleChange}
                  className={getInputClass('date_of_birth')}
                />
                {validationErrors.date_of_birth && <p className="text-red-500 text-xs mt-1">{validationErrors.date_of_birth}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Address *</label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  rows="2"
                  className={getInputClass('address')}
                  placeholder="Flat No, Street Name"
                />
                {validationErrors.address && <p className="text-red-500 text-xs mt-1">{validationErrors.address}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  className={getInputClass('city')}
                />
                {validationErrors.city && <p className="text-red-500 text-xs mt-1">{validationErrors.city}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State *</label>
                <input
                  type="text"
                  name="state"
                  value={formData.state}
                  onChange={handleChange}
                  className={getInputClass('state')}
                />
                {validationErrors.state && <p className="text-red-500 text-xs mt-1">{validationErrors.state}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pincode *</label>
                <input
                  type="text"
                  name="pincode"
                  value={formData.pincode}
                  onChange={handleChange}
                  className={getInputClass('pincode')}
                  maxLength="6"
                  placeholder="123456"
                />
                {validationErrors.pincode && <p className="text-red-500 text-xs mt-1">{validationErrors.pincode}</p>}
              </div>
            </div>

            <button
              onClick={nextStep}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 mt-4 transition-colors shadow-md"
            >
              Next Step →
            </button>
          </div>
        )}

        {/* Step 2: Employment Information */}
        {step === 2 && (
          <div className="space-y-4 animate-fadeIn">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Employment Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Occupation *</label>
                <input
                  type="text"
                  name="occupation"
                  value={formData.occupation}
                  onChange={handleChange}
                  className={getInputClass('occupation')}
                  placeholder="Software Engineer"
                />
                {validationErrors.occupation && <p className="text-red-500 text-xs mt-1">{validationErrors.occupation}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employer Name *</label>
                <input
                  type="text"
                  name="employer_name"
                  value={formData.employer_name}
                  onChange={handleChange}
                  className={getInputClass('employer_name')}
                  placeholder="Company Name"
                />
                {validationErrors.employer_name && <p className="text-red-500 text-xs mt-1">{validationErrors.employer_name}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Years at Job *</label>
                <input
                  type="number"
                  name="employment_years"
                  value={formData.employment_years}
                  onChange={handleChange}
                  className={getInputClass('employment_years')}
                  min="0"
                />
                {validationErrors.employment_years && <p className="text-red-500 text-xs mt-1">{validationErrors.employment_years}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Annual Income (₹) *</label>
                <input
                  type="number"
                  name="annual_income"
                  value={formData.annual_income}
                  onChange={handleChange}
                  className={getInputClass('annual_income')}
                  min="0"
                />
                {validationErrors.annual_income && <p className="text-red-500 text-xs mt-1">{validationErrors.annual_income}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Expenses (₹) *</label>
                <input
                  type="number"
                  name="monthly_expenses"
                  value={formData.monthly_expenses}
                  onChange={handleChange}
                  className={getInputClass('monthly_expenses')}
                  min="0"
                />
                {validationErrors.monthly_expenses && <p className="text-red-500 text-xs mt-1">{validationErrors.monthly_expenses}</p>}
              </div>
            </div>

            <div className="flex gap-4 mt-4">
              <button onClick={prevStep} className="flex-1 border border-gray-300 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors">
                ← Back
              </button>
              <button onClick={nextStep} className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md">
                Next Step →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Financial Information */}
        {step === 3 && (
          <form onSubmit={handleRegister} className="space-y-4 animate-fadeIn">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Financial Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Account Balance (₹)</label>
                <input
                  type="number"
                  name="account_balance"
                  value={formData.account_balance}
                  onChange={handleChange}
                  className={getInputClass('account_balance')}
                  min="0"
                />
                {validationErrors.account_balance && <p className="text-red-500 text-xs mt-1">{validationErrors.account_balance}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mutual Funds (₹)</label>
                <input
                  type="number"
                  name="mutual_funds"
                  value={formData.mutual_funds}
                  onChange={handleChange}
                  className={getInputClass('mutual_funds')}
                  min="0"
                />
                {validationErrors.mutual_funds && <p className="text-red-500 text-xs mt-1">{validationErrors.mutual_funds}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stocks (₹)</label>
                <input
                  type="number"
                  name="stocks"
                  value={formData.stocks}
                  onChange={handleChange}
                  className={getInputClass('stocks')}
                  min="0"
                />
                 {validationErrors.stocks && <p className="text-red-500 text-xs mt-1">{validationErrors.stocks}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fixed Deposits (₹)</label>
                <input
                  type="number"
                  name="fixed_deposits"
                  value={formData.fixed_deposits}
                  onChange={handleChange}
                  className={getInputClass('fixed_deposits')}
                  min="0"
                />
                 {validationErrors.fixed_deposits && <p className="text-red-500 text-xs mt-1">{validationErrors.fixed_deposits}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Existing Loans Count</label>
                <input
                  type="number"
                  name="existing_loans"
                  value={formData.existing_loans}
                  onChange={handleChange}
                  className={getInputClass('existing_loans')}
                  min="0"
                />
                 {validationErrors.existing_loans && <p className="text-red-500 text-xs mt-1">{validationErrors.existing_loans}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Existing Loan Amount (₹)</label>
                <input
                  type="number"
                  name="existing_loan_amount"
                  value={formData.existing_loan_amount}
                  onChange={handleChange}
                  className={getInputClass('existing_loan_amount')}
                  min="0"
                />
                 {validationErrors.existing_loan_amount && <p className="text-red-500 text-xs mt-1">{validationErrors.existing_loan_amount}</p>}
              </div>
            </div>

            <div className="flex gap-4 mt-4">
              <button type="button" onClick={prevStep} className="flex-1 border border-gray-300 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors">
                ← Back
              </button>
              <button 
                type="submit" 
                disabled={loading} 
                className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors shadow-md"
              >
                {loading ? 'Registering...' : 'Complete Registration'}
              </button>
            </div>
          </form>
        )}

        {/* Step 4: OTP Verification */}
        {step === 4 && (
          <form onSubmit={handleVerifyOTP} className="space-y-4 animate-fadeIn">
            <h2 className="text-xl font-semibold mb-4 text-center text-gray-800">Verify Your Email</h2>
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <p className="text-gray-600">
                We've sent a 6-digit code to <br/>
                <span className="font-semibold text-blue-700">{formData.email}</span>
              </p>
            </div>
            
            <div>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-center text-2xl tracking-widest font-mono"
                placeholder="000000"
                maxLength={6}
                required
              />
              <p className="text-xs text-gray-500 mt-2 text-center">
                * Check your backend console for the OTP
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-md"
            >
              {loading ? 'Verifying...' : 'Verify & Log In'}
            </button>
          </form>
        )}

        <div className="mt-6 text-center border-t pt-4">
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