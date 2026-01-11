import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { Shield, Moon, Sun, LogOut, User, LayoutDashboard, ChevronDown } from 'lucide-react';

export default function Navbar() {
    const { user, logout } = useAuth();
    const { darkMode, toggleDarkMode } = useTheme();
    const navigate = useNavigate();
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const dashboardPath = user?.role === 'admin' ? '/admin' : '/dashboard';
    const initials = user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U';

    return (
        <>
            <nav className="border-b bg-card sticky top-0 z-[100] shadow-sm">
                <div className="w-full px-4">
                    <div className="flex justify-between items-center h-16">
                        {/* Logo - Left aligned */}
                        <Link to={dashboardPath} className="flex items-center gap-3 hover:opacity-80 transition">
                            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-sm">
                                <Shield className="w-6 h-6 text-primary-foreground" />
                            </div>
                            <div>
                                <span className="text-xl font-bold tracking-tight">RISKOFF</span>
                                <span className="hidden sm:inline text-xs text-muted-foreground ml-2">
                                    {user?.role === 'admin' ? 'Admin Portal' : 'Loan Management'}
                                </span>
                            </div>
                        </Link>

                        {/* Right side */}
                        <div className="flex items-center gap-3">
                            {/* Theme Toggle */}
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={toggleDarkMode}
                                className="rounded-full hover:bg-muted"
                            >
                                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                            </Button>

                            {/* User Dropdown */}
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" className="flex items-center gap-2 px-2 h-11 hover:bg-muted">
                                        <Avatar className="h-8 w-8">
                                            <AvatarFallback className="bg-primary text-primary-foreground text-sm font-semibold">
                                                {initials}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div className="hidden md:block text-left">
                                            <p className="text-sm font-semibold leading-tight">{user?.full_name || 'User'}</p>
                                            <p className="text-xs text-muted-foreground capitalize">{user?.role || 'user'}</p>
                                        </div>
                                        <ChevronDown className="w-4 h-4 text-muted-foreground hidden md:block" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent
                                    align="end"
                                    sideOffset={8}
                                    className="w-56 bg-white dark:bg-zinc-900 border shadow-xl"
                                    style={{ zIndex: 9999 }}
                                >
                                    <DropdownMenuLabel className="font-normal">
                                        <div className="flex flex-col space-y-1">
                                            <p className="text-sm font-medium leading-none">{user?.full_name}</p>
                                            <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
                                        </div>
                                    </DropdownMenuLabel>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={() => navigate(dashboardPath)} className="cursor-pointer">
                                        <LayoutDashboard className="mr-2 h-4 w-4" />
                                        Dashboard
                                    </DropdownMenuItem>
                                    {user?.role !== 'admin' && (
                                        <DropdownMenuItem onClick={() => navigate('/profile')} className="cursor-pointer">
                                            <User className="mr-2 h-4 w-4" />
                                            Profile
                                        </DropdownMenuItem>
                                    )}
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                        onClick={() => setShowLogoutConfirm(true)}
                                        className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50 dark:focus:bg-red-900/20"
                                    >
                                        <LogOut className="mr-2 h-4 w-4" />
                                        Logout
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Logout Confirmation Dialog */}
            <ConfirmDialog
                open={showLogoutConfirm}
                onOpenChange={setShowLogoutConfirm}
                title="Confirm Logout"
                description="Are you sure you want to log out? You will need to sign in again to access your account."
                confirmText="Logout"
                cancelText="Stay Signed In"
                variant="warning"
                onConfirm={handleLogout}
            />
        </>
    );
}
