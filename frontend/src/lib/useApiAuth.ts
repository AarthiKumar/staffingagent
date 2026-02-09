import { useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { apiClient } from './api';

const audience = import.meta.env.VITE_AUTH0_AUDIENCE as string;

/**
 * Wires the Auth0 token getter into the API client.
 * Mount this once at the app level.
 */
export function useApiAuth() {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  useEffect(() => {
    if (isAuthenticated) {
      apiClient.setTokenGetter(() =>
        getAccessTokenSilently({ authorizationParams: { audience } })
      );
    }
  }, [isAuthenticated, getAccessTokenSilently]);
}
