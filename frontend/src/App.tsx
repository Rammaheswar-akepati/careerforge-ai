import { AuthPanel } from "./components/AuthPanel";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ResumeDashboard } from "./components/ResumeDashboard";

function AuthenticatedApp() {
  const { user } = useAuth();

  if (!user) {
    return <AuthPanel />;
  }

  return <ResumeDashboard />;
}

function App() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}

export default App;
