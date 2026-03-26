import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { demoLogin as apiDemoLogin, getMe, login as apiLogin, register as apiRegister, UserOut } from "../api/auth";

const TOKEN_KEY = "erpforge_token";

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string, role: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const resp = await apiLogin(email, password);
    localStorage.setItem(TOKEN_KEY, resp.access_token);
    setUser(resp.user);
  }, []);

  const register = useCallback(
    async (email: string, password: string, displayName: string, role: string) => {
      const resp = await apiRegister(email, password, displayName, role);
      localStorage.setItem(TOKEN_KEY, resp.access_token);
      setUser(resp.user);
    },
    []
  );

  const demoLogin = useCallback(async () => {
    const resp = await apiDemoLogin();
    localStorage.setItem(TOKEN_KEY, resp.access_token);
    setUser(resp.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, demoLogin, logout, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export { TOKEN_KEY };
