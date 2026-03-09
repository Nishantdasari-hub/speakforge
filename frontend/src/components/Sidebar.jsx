import { NavLink } from "react-router-dom";
import {
  FaHome,
  FaClipboardList,
  FaQuestionCircle,
  FaChartLine
} from "react-icons/fa";

export default function Sidebar() {

  const menuItem =
    "flex items-center gap-3 p-3 rounded-lg text-gray-300 hover:bg-blue-600 hover:text-white transition duration-200";

  const activeMenu =
    "bg-blue-600 text-white";

  return (

    <div className="w-64 min-h-screen bg-gray-950 border-r border-gray-800 flex flex-col">

      {/* Logo Section */}

      <div className="p-6 border-b border-gray-800">

        <h1 className="text-2xl font-bold text-white">
          SpeakForge
        </h1>

        <p className="text-xs text-gray-400">
          AI Speaking Platform
        </p>

      </div>


      {/* Navigation */}

      <nav className="flex-1 p-4 space-y-2">

        <NavLink
          to="/admin/dashboard"
          className={({ isActive }) =>
            `${menuItem} ${isActive ? activeMenu : ""}`
          }
        >
          <FaHome />
          Dashboard
        </NavLink>


        <NavLink
          to="/admin/tests"
          className={({ isActive }) =>
            `${menuItem} ${isActive ? activeMenu : ""}`
          }
        >
          <FaClipboardList />
          Tests
        </NavLink>


        <NavLink
          to="/admin/questions"
          className={({ isActive }) =>
            `${menuItem} ${isActive ? activeMenu : ""}`
          }
        >
          <FaQuestionCircle />
          Questions
        </NavLink>


        <NavLink
          to="/admin/analytics"
          className={({ isActive }) =>
            `${menuItem} ${isActive ? activeMenu : ""}`
          }
        >
          <FaChartLine />
          Analytics
        </NavLink>

      </nav>


      {/* Footer */}

      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
        SpeakForge AI
      </div>

    </div>

  );

}