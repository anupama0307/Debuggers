import { useState, useEffect } from 'react';
import Navbar from '@/components/common/Navbar';
import Sidebar from '@/components/common/Sidebar';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { ClipboardList, CheckCircle, XCircle, AlertCircle, User } from 'lucide-react';
import api from '@/services/api';

interface Loan {
    id: string;
    user_name?: string;
    full_name?: string;
    user_email?: string;
    email?: string;
    purpose?: string;
    amount?: number;
    loan_amount?: number;
    risk_category?: string;
    risk_score?: number;
    status?: string;
    created_at?: string;
}

export default function LoanApplicationsPage() {
    const [loans, setLoans] = useState<Loan[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [error, setError] = useState('');
    const [confirmAction, setConfirmAction] = useState<{ loanId: string; action: 'APPROVED' | 'REJECTED'; name: string; amount: number } | null>(null);

    useEffect(() => { fetchLoans(); }, []);

    const fetchLoans = async () => {
        try {
            setError('');
            const response = await api.get('/admin/loans');
            const loansData = response.data?.loans || response.data || [];
            setLoans(Array.isArray(loansData) ? loansData : []);
        } catch (err: any) {
            if (err.response?.status === 403) setError('Access denied. Admin privileges required.');
            else if (err.response?.status === 401) setError('Session expired. Please login again.');
            else setError(err.response?.data?.detail || 'Failed to load loans. Please try again.');
            setLoans([]);
        } finally {
            setLoading(false);
        }
    };

    const filteredLoans = filter === 'all'
        ? loans
        : loans.filter(loan => (loan.status || 'pending').toLowerCase() === filter.toLowerCase());

    const handleStatusUpdate = async (loanId: string, newStatus: string) => {
        try {
            setError('');
            await api.patch(`/admin/loans/${loanId}/status`, {
                loan_id: loanId,
                status: newStatus.toUpperCase(),
                remarks: `${newStatus} by admin`
            });
            fetchLoans();
        } catch (err: any) {
            if (err.response?.status === 404) {
                setError('Loan not found. It may have been deleted.');
            } else if (err.response?.status === 400) {
                setError('Invalid request. The loan may already be processed.');
            } else {
                setError(err.response?.data?.detail || 'Failed to update loan status. Please try again.');
            }
        }
    };

    const onActionClick = (loan: Loan, action: 'APPROVED' | 'REJECTED') => {
        setConfirmAction({
            loanId: loan.id,
            action,
            name: loan.user_name || loan.full_name || 'Unknown',
            amount: loan.amount || loan.loan_amount || 0
        });
    };

    const handleConfirmedAction = () => {
        if (confirmAction) {
            handleStatusUpdate(confirmAction.loanId, confirmAction.action);
            setConfirmAction(null);
        }
    };

    const getStatusStyle = (status: string) => {
        const s = status?.toLowerCase();
        if (s === 'approved') return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
        if (s === 'rejected') return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    };

    const getRiskStyle = (category: string) => {
        if (category === 'LOW') return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
        if (category === 'MEDIUM') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
        if (category === 'HIGH') return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
        return 'bg-muted text-muted-foreground';
    };

    if (loading) {
        return <div className="min-h-screen bg-background"><Navbar /><div className="flex"><Sidebar /><main className="flex-1 p-8"><LoadingSpinner /></main></div></div>;
    }

    const filterButtons = [
        { key: 'all', label: 'All', count: loans.length },
        { key: 'pending', label: 'Pending', count: loans.filter(l => l.status?.toLowerCase() === 'pending').length },
        { key: 'approved', label: 'Approved', count: loans.filter(l => l.status?.toLowerCase() === 'approved').length },
        { key: 'rejected', label: 'Rejected', count: loans.filter(l => l.status?.toLowerCase() === 'rejected').length },
    ];

    return (
        <div className="min-h-screen bg-background">
            <Navbar />
            <div className="flex">
                <Sidebar />
                <main className="flex-1 p-8">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h1 className="text-3xl font-bold">Loan Applications</h1>
                            <p className="text-lg text-muted-foreground mt-1">{filteredLoans.length} applications</p>
                        </div>
                    </div>

                    <div className="flex gap-2 mb-6">
                        {filterButtons.map((f) => (
                            <Button
                                key={f.key}
                                variant={filter === f.key ? 'default' : 'secondary'}
                                onClick={() => setFilter(f.key)}
                                className="gap-2"
                            >
                                {f.label}
                                <span className="bg-primary-foreground/20 px-2 py-0.5 rounded-full text-xs">{f.count}</span>
                            </Button>
                        ))}
                    </div>

                    {error && (
                        <div className="mb-6 p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg flex items-center gap-2">
                            <AlertCircle className="w-5 h-5" /> {error}
                        </div>
                    )}

                    {filteredLoans.length === 0 ? (
                        <Card className="text-center py-16">
                            <CardContent>
                                <ClipboardList className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
                                <p className="text-xl font-medium mb-2">No {filter === 'all' ? '' : filter} loan applications</p>
                                <p className="text-muted-foreground">Applications will appear here when users apply</p>
                            </CardContent>
                        </Card>
                    ) : (
                        <Card>
                            <CardContent className="p-0">
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-muted">
                                            <tr>
                                                <th className="px-4 py-4 text-left text-sm font-semibold text-muted-foreground">ID</th>
                                                <th className="px-4 py-4 text-left text-sm font-semibold text-muted-foreground">Customer</th>
                                                <th className="px-4 py-4 text-left text-sm font-semibold text-muted-foreground">Purpose</th>
                                                <th className="px-4 py-4 text-left text-sm font-semibold text-muted-foreground">Amount</th>
                                                <th className="px-4 py-4 text-left text-sm font-semibold text-muted-foreground">Risk</th>
                                                <th className="px-4 py-4 text-left text-sm font-semibold text-muted-foreground">Status</th>
                                                <th className="px-4 py-4 text-left text-sm font-semibold text-muted-foreground">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-border">
                                            {filteredLoans.map((loan) => (
                                                <tr key={loan.id} className="hover:bg-muted/50 transition">
                                                    <td className="px-4 py-4 text-sm font-medium">#{loan.id}</td>
                                                    <td className="px-4 py-4">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-9 h-9 bg-muted rounded-full flex items-center justify-center">
                                                                <User className="w-5 h-5 text-muted-foreground" />
                                                            </div>
                                                            <div>
                                                                <p className="text-sm font-medium">{loan.user_name || loan.full_name || 'N/A'}</p>
                                                                <p className="text-xs text-muted-foreground">{loan.user_email || loan.email || ''}</p>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-4 text-sm capitalize">{loan.purpose || 'General'}</td>
                                                    <td className="px-4 py-4 text-sm font-semibold">₹{(loan.amount || loan.loan_amount || 0).toLocaleString('en-IN')}</td>
                                                    <td className="px-4 py-4">
                                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskStyle(loan.risk_category || '')}`}>
                                                            {loan.risk_category || 'N/A'}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-4">
                                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusStyle(loan.status || 'pending')}`}>
                                                            {(loan.status || 'PENDING').toUpperCase()}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-4">
                                                        {(loan.status?.toUpperCase() === 'PENDING' || !loan.status) ? (
                                                            <div className="flex gap-2">
                                                                <Button
                                                                    size="sm"
                                                                    variant="ghost"
                                                                    className="h-9 bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400 gap-1"
                                                                    onClick={() => onActionClick(loan, 'APPROVED')}
                                                                >
                                                                    <CheckCircle className="w-4 h-4" /> Approve
                                                                </Button>
                                                                <Button
                                                                    size="sm"
                                                                    variant="ghost"
                                                                    className="h-9 bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 gap-1"
                                                                    onClick={() => onActionClick(loan, 'REJECTED')}
                                                                >
                                                                    <XCircle className="w-4 h-4" /> Reject
                                                                </Button>
                                                            </div>
                                                        ) : (
                                                            <span className="text-sm text-muted-foreground">—</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </main>
            </div>

            {/* Confirmation Dialog for Approve/Reject */}
            <ConfirmDialog
                open={!!confirmAction}
                onOpenChange={(open) => !open && setConfirmAction(null)}
                title={confirmAction?.action === 'APPROVED' ? 'Approve Loan Application' : 'Reject Loan Application'}
                description={
                    confirmAction?.action === 'APPROVED'
                        ? `Are you sure you want to approve the loan of ₹${confirmAction.amount.toLocaleString('en-IN')} for ${confirmAction.name}? This action cannot be undone.`
                        : `Are you sure you want to reject the loan of ₹${confirmAction?.amount.toLocaleString('en-IN')} for ${confirmAction?.name}? The applicant will be notified.`
                }
                confirmText={confirmAction?.action === 'APPROVED' ? 'Approve Loan' : 'Reject Loan'}
                cancelText="Cancel"
                variant={confirmAction?.action === 'APPROVED' ? 'info' : 'danger'}
                onConfirm={handleConfirmedAction}
            />
        </div>
    );
}
