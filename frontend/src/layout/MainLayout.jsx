import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

export default function MainLayout({ children }) {

  return (

    <div className="flex min-h-screen bg-gray-950">

      {/* Sidebar */}

      <Sidebar />


      {/* Main Area */}

      <div className="flex flex-col flex-1">

        {/* Top Navbar */}

        <Navbar />


        {/* Page Content */}

        <main className="flex-1 p-8 bg-gradient-to-br from-gray-950 via-slate-900 to-black text-white">

          {children}

        </main>

      </div>

    </div>

  );

}