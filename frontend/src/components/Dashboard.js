import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get('/api/dashboard');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const formatChartData = (data) => {
    const labels = data.map((item) => item.date);
    const correctCountsByLoke = data
      .filter((item) => item.user === 'loke')
      .map((item) => item.total_correct_count);
    const correctCountsByAdarsh = data
      .filter((item) => item.user === 'adarsh')
      .map((item) => item.total_correct_count);
    const incorrectCountsByLoke = data
      .filter((item) => item.user === 'loke')
      .map((item) => item.total_incorrect_count);
    const incorrectCountsByAdarsh = data
      .filter((item) => item.user === 'adarsh')
      .map((item) => item.total_incorrect_count);

    return {
      labels,
      datasets: [
        {
          label: 'Correct Word Counts by Loke',
          data: correctCountsByLoke,
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          fill: true,
        },
        {
          label: 'Correct Word Counts by Adarsh',
          data: correctCountsByAdarsh,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: true,
        },
        {
          label: 'Incorrect Word Counts by Loke',
          data: incorrectCountsByLoke,
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          fill: true,
        },
        {
          label: 'Incorrect Word Counts by Adarsh',
          data: incorrectCountsByAdarsh,
          borderColor: 'rgba(255, 159, 64, 1)',
          backgroundColor: 'rgba(255, 159, 64, 0.2)',
          fill: true,
        },
      ],
    };
  };

  return (
    <div>
      <h1>Dashboard</h1>
      {dashboardData ? (
        <Line data={formatChartData(dashboardData)} />
      ) : (
        <p>Loading dashboard data...</p>
      )}
    </div>
  );
};

export default Dashboard;
