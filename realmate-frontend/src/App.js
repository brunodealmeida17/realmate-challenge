import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Conversations from "./pages/Conversations";


export default function App() {
  return (
    <Router>
      <div className="container">
        <Routes>
          <Route path="/" element={<Conversations />} />
          
        </Routes>
      </div>
    </Router>
  );
}
