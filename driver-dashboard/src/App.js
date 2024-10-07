// App.js
import React from 'react';
import './App.css';

function App() {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="dashboard-title">Welcome to the Driver Dashboard, Jayde!</h1>
        <nav className="dashboard-nav">
          <ul>
            <li><a href="#">Home</a></li>
            <li><a href="#">Messages</a></li>
            <li><a href="#">Points</a></li>
            <li><a href="#">Catalog</a></li>
            <li><a href="#">Purchases</a></li>
            <li><a href="#">Trips</a></li>
            <li><a href="#">Logout</a></li>
          </ul>
        </nav>
      </header>

      <main className="dashboard-main">
        <section className="trip-section">
          <h2>Your Trips</h2>
          <table className="trip-table">
            <thead>
              <tr>
                <th>Trip ID</th>
                <th>Destination</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {/* Render trips dynamically here */}
              <tr>
                <td>001</td>
                <td>New York</td>
                <td>Completed</td>
              </tr>
              <tr>
                <td>002</td>
                <td>Chicago</td>
                <td>In Progress</td>
              </tr>
              <tr>
                <td>003</td>
                <td>Los Angeles</td>
                <td>Upcoming</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="points-section">
          <h2>Your Points</h2>
          <p>Total Points: <strong>1500</strong></p>
        </section>
      </main>

      <footer className="dashboard-footer">
        <p>&copy; 2024 Driver Dashboard. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
