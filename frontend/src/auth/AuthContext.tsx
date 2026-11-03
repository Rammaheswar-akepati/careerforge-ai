import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  loginUser,
  type LoginRequest,
  type User,
} from "../api/auth";

interface AuthContextValue {
  accessToken: string | null;
  user: User | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const logout = useCallback(() => {
    setUser(null);
    setAccessToken(null);
  }, []);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      const tokenResponse = await loginUser(credentials);
      const currentUser = await getCurrentUser(tokenResponse.access_token, logout);
      setAccessToken(tokenResponse.access_token);
      setUser(currentUser);
    },
    [logout],
  );

  const value = useMemo(
    () => ({ accessToken, user, login, logout }),
    [accessToken, user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }
  return context;
}
