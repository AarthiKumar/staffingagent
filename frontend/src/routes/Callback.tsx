import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';

/**
 * Auth0 callback page - handles the redirect after authentication
 */
export function Callback() {
  const { isAuthenticated, isLoading, error } = useAuth0();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        // Redirect to home page after successful authentication
        navigate('/');
      } else if (error) {
        // Redirect to home with error
        console.error('Authentication error:', error);
        navigate('/?auth_error=true');
      }
    }
  }, [isLoading, isAuthenticated, error, navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="text-center">
        {isLoading && (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Completing Sign In</h2>
            <p className="text-gray-600">Please wait while we log you in...</p>
          </>
        )}

        {error && (
          <div className="max-w-md p-8 bg-white rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h2>
            <p className="text-gray-700 mb-4">{error.message}</p>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go to Home
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
