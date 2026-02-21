/*
File Logic Summary: TypeScript module for frontend runtime logic, routing, API integration, or UI behavior.
*/

import Sidebar from "../components/Sidebar";

export default function Profile() {
  const user = localStorage.getItem("user");
  const parsed = user ? JSON.parse(user) : null;

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-content">
        <div className="dashboard-header">
          <div className="header-top">
            <h1>Profile</h1>
          </div>
          <p className="header-subtitle">
            {parsed?.email ? `Signed in as ${parsed.email}` : "No user details available."}
          </p>
        </div>
      </main>
    </div>
  );
}

