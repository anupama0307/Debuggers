import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '@/components/common/Navbar';
import Sidebar from '@/components/common/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { Wallet, IndianRupee, Calendar, TrendingUp, TrendingDown, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import api from '@/services/api';

export default function ApplyLoanPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showConfirm, setShowConfirm] = useState(false);
    const [formData, setFormData] = useState({
        amount: '',
        tenure_months: '',
        monthly_income: '',
        monthly_expenses: '',
        purpose: ''
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const validateForm = () => {
        const amount = parseFloat(formData.amount);
        const tenure = parseInt(formData.tenure_months);
        const income = parseFloat(formData.monthly_income);
        const expenses = parseFloat(formData.monthly_expenses);

        if (amount < 10000) {
            setError('Minimum loan amount is Rs. 10,000');
            return false;
        }
        if (tenure < 6 || tenure > 60) {
            setError('Tenure must be between 6 and 60 months');
            return false;
        }
        if (income <= 0) {
            setError('Please enter a valid monthly income');
            return false;
        }
        if (expenses < 0) {
            setError('Monthly expenses cannot be negative');
            return false;
        }
        if (formData.purpose.length < 3) {
            setError('Please specify the purpose of the loan');
            return false;
        }
        return true;
    };

    const handleSubmitClick = (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (validateForm()) {
            setShowConfirm(true);
        }
    };

    const handleConfirmedSubmit = async () => {
        setShowConfirm(false);
        setLoading(true);

        try {
            const payload = {
                amount: parseFloat(formData.amount),
                tenure_months: parseInt(formData.tenure_months),
                monthly_income: parseFloat(formData.monthly_income),
                monthly_expenses: parseFloat(formData.monthly_expenses),
                purpose: formData.purpose.trim()
            };

            const response = await api.post('/loans/apply', payload);
            console.log('Loan application response:', response.data);

            setSuccess('Loan application submitted successfully! Redirecting to My Loans...');
            setTimeout(() => navigate('/my-loans'), 2000);
        } catch (err: any) {
            console.error('Loan application error:', err.response?.data);
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                setError(detail);
            } else if (Array.isArray(detail)) {
                setError(detail.map((d: any) => d.msg).join(', '));
            } else if (err.message) {
                setError(`Network error: ${err.message}. Please check your connection.`);
            } else {
                setError('Failed to submit application. Please try again later.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background">
            <Navbar />
            <div className="flex">
                <Sidebar />
                <main className="flex-1 p-8">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold">Apply for Loan</h1>
                        <p className="text-lg text-muted-foreground mt-1">Fill in the details to submit your loan application</p>
                    </div>

                    {success && (
                        <div className="mb-6 p-4 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-lg flex items-center gap-2">
                            <CheckCircle className="w-5 h-5 flex-shrink-0" />
                            <span className="text-base">{success}</span>
                        </div>
                    )}

                    {error && (
                        <div className="mb-6 p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg flex items-center gap-2">
                            <AlertCircle className="w-5 h-5 flex-shrink-0" />
                            <span className="text-base">{error}</span>
                        </div>
                    )}

                    <div className="max-w-2xl">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-3 text-xl">
                                    <Wallet className="w-6 h-6" />
                                    Loan Application Form
                                </CardTitle>
                                <CardDescription className="text-base">All fields are required</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleSubmitClick} className="space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <Label className="text-base font-medium">Loan Amount (Rs.)</Label>
                                            <div className="relative mt-2">
                                                <IndianRupee className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                                                <Input
                                                    name="amount"
                                                    type="number"
                                                    value={formData.amount}
                                                    onChange={handleChange}
                                                    placeholder="50000"
                                                    required
                                                    min="10000"
                                                    className="h-12 pl-12 text-base"
                                                />
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1">Min: Rs. 10,000</p>
                                        </div>

                                        <div>
                                            <Label className="text-base font-medium">Tenure (Months)</Label>
                                            <div className="relative mt-2">
                                                <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                                                <Input
                                                    name="tenure_months"
                                                    type="number"
                                                    value={formData.tenure_months}
                                                    onChange={handleChange}
                                                    placeholder="12"
                                                    required
                                                    min="6"
                                                    max="60"
                                                    className="h-12 pl-12 text-base"
                                                />
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1">6 to 60 months</p>
                                        </div>

                                        <div>
                                            <Label className="text-base font-medium">Monthly Income (Rs.)</Label>
                                            <div className="relative mt-2">
                                                <TrendingUp className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                                                <Input
                                                    name="monthly_income"
                                                    type="number"
                                                    value={formData.monthly_income}
                                                    onChange={handleChange}
                                                    placeholder="50000"
                                                    required
                                                    min="1"
                                                    className="h-12 pl-12 text-base"
                                                />
                                            </div>
                                        </div>

                                        <div>
                                            <Label className="text-base font-medium">Monthly Expenses (Rs.)</Label>
                                            <div className="relative mt-2">
                                                <TrendingDown className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                                                <Input
                                                    name="monthly_expenses"
                                                    type="number"
                                                    value={formData.monthly_expenses}
                                                    onChange={handleChange}
                                                    placeholder="25000"
                                                    required
                                                    min="0"
                                                    className="h-12 pl-12 text-base"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <Label className="text-base font-medium">Purpose of Loan</Label>
                                        <div className="relative mt-2">
                                            <FileText className="absolute left-4 top-4 w-5 h-5 text-muted-foreground" />
                                            <textarea
                                                name="purpose"
                                                value={formData.purpose}
                                                onChange={handleChange}
                                                placeholder="e.g., Business expansion, Home renovation, Medical expenses..."
                                                required
                                                rows={3}
                                                className="w-full rounded-lg border border-input pl-12 pr-4 py-3 text-base bg-background"
                                            />
                                        </div>
                                    </div>

                                    <Button type="submit" size="lg" className="w-full h-12 text-base gap-2" disabled={loading}>
                                        {loading ? (
                                            <>
                                                <Loader2 className="w-5 h-5 animate-spin" />
                                                Submitting Application...
                                            </>
                                        ) : (
                                            <>
                                                <Wallet className="w-5 h-5" />
                                                Submit Application
                                            </>
                                        )}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>
                    </div>
                </main>
            </div>

            {/* Confirmation Dialog */}
            <ConfirmDialog
                open={showConfirm}
                onOpenChange={setShowConfirm}
                title="Confirm Loan Application"
                description={`You are about to submit a loan application for Rs. ${parseFloat(formData.amount || '0').toLocaleString('en-IN')} for ${formData.tenure_months || 0} months. This will be reviewed by our team. Do you want to proceed?`}
                confirmText="Submit Application"
                cancelText="Review Details"
                variant="info"
                onConfirm={handleConfirmedSubmit}
            />
        </div>
    );
}
