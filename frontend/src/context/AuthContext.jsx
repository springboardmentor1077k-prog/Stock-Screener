import { createContext, useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  const login = (token) => {
    try {
      const decoded = jwtDecode(token);

      localStorage.setItem("token", token);

      setUser({
        token,
        id: decoded.id,
        email: decoded.email,
        exp: decoded.exp,
      });

    } catch (error) {
      console.error("Invalid token during login");
      logout();
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) return;

    try {
      const decoded = jwtDecode(token);
      const currentTime = Date.now() / 1000;

      if (decoded.exp < currentTime) {
        logout(); // Token expired
      } else {
        setUser({
          token,
          id: decoded.id,
          email: decoded.email,
          exp: decoded.exp,
        });
      }
    } catch (error) {
      logout();
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};