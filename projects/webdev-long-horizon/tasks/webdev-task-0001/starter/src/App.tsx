import { Link, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import MerchantDetail from './pages/MerchantDetail';
import OrderSuccess from './pages/OrderSuccess';
import Home from './pages/Home';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-[#F5F7FA]">
        <header className="border-b border-gray-200 bg-white">
          <div className="mx-auto flex max-w-[1440px] items-center justify-between px-6 py-4">
            <Link to="/" className="text-xl font-bold text-[#1677FF]">
              本地生活
            </Link>
            <nav className="hidden items-center gap-6 md:flex">
              <Link to="/" className="text-gray-700 hover:text-[#1677FF]">首页</Link>
              <Link to="/" className="text-gray-700 hover:text-[#1677FF]">订单</Link>
            </nav>
            <button className="md:hidden text-gray-700">菜单</button>
          </div>
        </header>

        <main className="mx-auto max-w-[1440px] p-6">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/merchant/:id" element={<MerchantDetail />} />
            <Route path="/order-success" element={<OrderSuccess />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
