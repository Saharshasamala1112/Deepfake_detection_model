import { useState } from "react";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import "./App.css";

function App() {
  const [auth, setAuth] = useState(false);

  return auth ? (
    <Dashboard />
  ) : (
    <Login setAuth={setAuth} />
  );
}

export default App;