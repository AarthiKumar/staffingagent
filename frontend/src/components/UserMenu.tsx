import React, { useState } from 'react';
import { LogIn, LogOut, User as UserIcon, ChevronDown } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { UserRole } from '@/lib/types';

export function UserMenu() {
  const { isAuthenticated, isLoading, user, login, logout, hasRole } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => setIsOpen(false);
    if (isOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [isOpen]);

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 px-4 py-2">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
        <span className="text-sm text-gray-600">Loading...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <button
        onClick={login}
        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <LogIn className="w-4 h-4" />
        <span className="font-medium">Log In</span>
      </button>
    );
  }

  // Get user's role badge
  const getRoleBadge = () => {
    if (hasRole(UserRole.SUPERUSER)) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold bg-purple-100 text-purple-800 rounded">
          Superuser
        </span>
      );
    }
    if (hasRole(UserRole.PROJECT_MANAGER)) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
          PM
        </span>
      );
    }
    if (hasRole(UserRole.STAFF)) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold bg-green-100 text-green-800 rounded">
          Staff
        </span>
      );
    }
    return null;
  };

  return (
    <div className="relative">
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="flex items-center space-x-3 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
      >
        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
          <UserIcon className="w-5 h-5 text-white" />
        </div>
        <div className="flex flex-col items-start">
          <span className="text-sm font-medium text-gray-900">{user?.name || user?.email}</span>
          {getRoleBadge()}
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-600 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-900">{user?.name || 'User'}</p>
            <p className="text-xs text-gray-500 mt-1">{user?.email}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {user?.roles.map((role) => (
                <span
                  key={role}
                  className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded"
                >
                  {role}
                </span>
              ))}
            </div>
          </div>

          {/* Logout Button */}
          <button
            onClick={() => {
              setIsOpen(false);
              logout();
            }}
            className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Log Out</span>
          </button>
        </div>
      )}
    </div>
  );
}
