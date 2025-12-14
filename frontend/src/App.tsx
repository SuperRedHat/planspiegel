import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./App.css";
import LoginPage from "./pages/LoginPage";
import RegistrationPage from "./pages/RegistrationPage";
import ProtectedRoute from "./components/Routes/ProtectedRoute";
import NotFoundPage from "./pages/NotFoundPage";
import URLPage from "./pages/URLPage";


function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/registration" element={<RegistrationPage />} />
        <Route path="/login/:errStatus?" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<URLPage />} />
          <Route path="/checkup/:checkup_id?" element={<URLPage />} />
          {/* <Route path="/profile" element={<UserPage />} /> */}
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
