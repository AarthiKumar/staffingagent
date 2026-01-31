import React, { createContext, useContext, ReactNode } from 'react';
import { useAuth0, Auth0Provider as BaseAuth0Provider } from '@auth0/auth0-react';
import { User, UserRole, AuthContextType } from './types';
import { AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_AUDIENCE, AUTH0_REDIRECT_URI } from './config';
import { apiClient } from './api';

const AuthContext = createContext<AuthContextType | null>(null);

/**
 * Custom hook to access Auth0 authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within Auth0ProviderWithConfig');
  }
  return context;
}

/**
 * Auth0 Provider wrapper that provides additional helpers
 */
function Auth0ProviderWrapper({ children }: { children: ReactNode }) {
  const {
    isAuthenticated,
    isLoading,
    user: auth0User,
    loginWithRedirect,
    logout: auth0Logout,
    getAccessTokenSilently,
  } = useAuth0();

  // Extract user info with roles from Auth0 user object
  const user: User | null = React.useMemo(() => {
    if (!auth0User) return null;

    return {
      sub: auth0User.sub || '',
      email: auth0User.email || '',
      name: auth0User.name,
      roles: (auth0User['https://staffingagent.com/roles'] as string[]) || [],
    };
  }, [auth0User]);

  // Set the token getter in the API client
  React.useEffect(() => {
    if (isAuthenticated) {
      apiClient.setTokenGetter(async () => {
        try {
          return await getAccessTokenSilently({
            authorizationParams: {
              audience: AUTH0_AUDIENCE,
            },
          });
        } catch (error) {
          console.error('Error getting access token:', error);
          return '';
        }
      });
    }
  }, [isAuthenticated, getAccessTokenSilently]);

  const login = () => {
    loginWithRedirect({
      authorizationParams: {
        audience: AUTH0_AUDIENCE,
        redirect_uri: AUTH0_REDIRECT_URI,
      },
    });
  };

  const logout = () => {
    auth0Logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  const getAccessToken = async (): Promise<string> => {
    try {
      return await getAccessTokenSilently({
        authorizationParams: {
          audience: AUTH0_AUDIENCE,
        },
      });
    } catch (error) {
      console.error('Error getting access token:', error);
      return '';
    }
  };

  const hasRole = (role: UserRole): boolean => {
    return user?.roles.includes(role) || false;
  };

  const hasAnyRole = (...roles: UserRole[]): boolean => {
    if (!user) return false;
    return roles.some((role) => user.roles.includes(role));
  };

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    getAccessToken,
    hasRole,
    hasAnyRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Auth0 Provider with configuration
 */
export function Auth0ProviderWithConfig({ children }: { children: ReactNode }) {
  if (!AUTH0_DOMAIN || !AUTH0_CLIENT_ID) {
    console.warn('Auth0 not configured. Running without authentication.');

    // Provide a mock auth context when Auth0 is not configured
    const mockValue: AuthContextType = {
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: () => console.warn('Auth0 not configured'),
      logout: () => console.warn('Auth0 not configured'),
      getAccessToken: async () => '',
      hasRole: () => false,
      hasAnyRole: () => false,
    };

    return <AuthContext.Provider value={mockValue}>{children}</AuthContext.Provider>;
  }

  return (
    <BaseAuth0Provider
      domain={AUTH0_DOMAIN}
      clientId={AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: AUTH0_REDIRECT_URI,
        audience: AUTH0_AUDIENCE,
      }}
      cacheLocation="localstorage"
    >
      <Auth0ProviderWrapper>{children}</Auth0ProviderWrapper>
    </BaseAuth0Provider>
  );
}

/**
 * Higher-order component to protect routes based on user roles
 */
export function withRequiredRole(Component: React.ComponentType<any>, requiredRole: UserRole) {
  return function ProtectedComponent(props: any) {
    const { isLoading, isAuthenticated, hasRole, login } = useAuth();

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading...</p>
          </div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center max-w-md p-8 bg-white rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">Authentication Required</h2>
            <p className="text-gray-600 mb-6">You must be logged in to access this page.</p>
            <button
              onClick={login}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Log In
            </button>
          </div>
        </div>
      );
    }

    if (!hasRole(requiredRole)) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center max-w-md p-8 bg-white rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold mb-4 text-red-600">Access Denied</h2>
            <p className="text-gray-600 mb-2">You don't have permission to access this page.</p>
            <p className="text-sm text-gray-500">Required role: {requiredRole}</p>
          </div>
        </div>
      );
    }

    return <Component {...props} />;
  };
}

/**
 * Component to protect routes based on authentication (any authenticated user)
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { isLoading, isAuthenticated, login } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md p-8 bg-white rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold mb-4 text-gray-900">Authentication Required</h2>
          <p className="text-gray-600 mb-6">You must be logged in to access this page.</p>
          <button
            onClick={login}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Log In
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
