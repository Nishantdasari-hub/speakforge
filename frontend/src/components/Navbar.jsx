export default function Navbar() {

  const logout = () => {
    for (const key of ["token", "role", "userEmail"]) localStorage.removeItem(key);
    window.location.href = "/";
  };

  const userEmail = localStorage.getItem("userEmail") || "User";
  const name = userEmail.split("@")[0];

  return (

    <div className="bg-gray-950 border-b border-gray-800 px-8 py-4 flex justify-between items-center">

      {/* Left */}

      <div>

        <h1 className="text-lg font-semibold text-white">
          Welcome back, {name} 👋
        </h1>

        <p className="text-xs text-gray-400">
          SpeakForge AI Dashboard
        </p>

      </div>


      {/* Right */}

      <button
        onClick={logout}
        className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition"
      >
        Logout
      </button>

    </div>

  );

}