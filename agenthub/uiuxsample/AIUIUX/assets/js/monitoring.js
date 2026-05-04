/* =============================================
   모니터링 페이지 - 차트 & 인터랙션
   ============================================= */

(function () {
  'use strict';

  const timeLabels = Array.from({ length: 24 }, (_, i) => i + ':00');

  // Throughput Chart
  const throughputCtx = document.getElementById('throughputCanvas');
  if (throughputCtx) {
    new Chart(throughputCtx, {
      type: 'line',
      data: {
        labels: timeLabels,
        datasets: [
          {
            label: 'GPT-4o',
            data: [820,750,680,610,890,1200,1580,1890,2100,2300,2480,2210,1980,2050,2180,2310,2400,2250,2100,1950,1800,1650,1520,1480],
            borderColor: '#4F46E5',
            backgroundColor: 'rgba(79,70,229,0.05)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
          {
            label: 'Claude',
            data: [480,420,380,350,490,710,940,1120,1280,1420,1520,1380,1260,1340,1390,1450,1520,1410,1340,1250,1180,1090,1020,980],
            borderColor: '#8B5CF6',
            backgroundColor: 'rgba(139,92,246,0.05)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
          {
            label: 'Gemini',
            data: [240,210,190,180,250,370,480,590,640,720,780,710,660,690,710,740,760,710,670,620,590,550,510,490],
            borderColor: '#10B981',
            backgroundColor: 'rgba(16,185,129,0.05)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(17,24,39,0.95)',
            titleColor: '#F9FAFB',
            bodyColor: '#D1D5DB',
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: ctx => ' ' + ctx.dataset.label + ': ' + ctx.parsed.y.toLocaleString() + ' req/min'
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            border: { display: false },
            ticks: { font: { size: 11 }, color: '#9CA3AF', maxTicksLimit: 8 }
          },
          y: {
            grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
            border: { display: false },
            ticks: { font: { size: 11 }, color: '#9CA3AF', callback: v => v.toLocaleString() }
          }
        }
      }
    });
  }

  // Error Rate Chart
  const errorCtx = document.getElementById('errorRateCanvas');
  if (errorCtx) {
    new Chart(errorCtx, {
      type: 'bar',
      data: {
        labels: timeLabels,
        datasets: [
          {
            label: '경고',
            data: [0,0,0,0,0,0.05,0.08,0.1,0.09,0.11,0.12,0.09,0.08,0.1,0.11,0.12,0.1,0.09,0.11,0.1,0.09,0.08,0.07,0.06],
            backgroundColor: 'rgba(245,158,11,0.6)',
            borderRadius: 2,
          },
          {
            label: '오류',
            data: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,1.2],
            backgroundColor: 'rgba(239,68,68,0.7)',
            borderRadius: 2,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: { usePointStyle: true, pointStyle: 'rect', font: { size: 11 }, color: '#6B7280', padding: 12 }
          },
          tooltip: {
            backgroundColor: 'rgba(17,24,39,0.95)',
            titleColor: '#F9FAFB',
            bodyColor: '#D1D5DB',
            padding: 10,
            cornerRadius: 8,
          }
        },
        scales: {
          x: {
            stacked: true,
            grid: { display: false },
            border: { display: false },
            ticks: { font: { size: 11 }, color: '#9CA3AF', maxTicksLimit: 8 }
          },
          y: {
            stacked: true,
            grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
            border: { display: false },
            ticks: { font: { size: 11 }, color: '#9CA3AF', callback: v => v + '%' }
          }
        }
      }
    });
  }

  // Latency Bar Chart
  const latencyCtx = document.getElementById('latencyCanvas');
  if (latencyCtx) {
    new Chart(latencyCtx, {
      type: 'bar',
      data: {
        labels: ['GPT-4o', 'Claude', 'Gemini'],
        datasets: [
          { label: 'P50', data: [152, 178, 241], backgroundColor: 'rgba(79,70,229,0.7)', borderRadius: 4 },
          { label: 'P95', data: [312, 389, 498], backgroundColor: 'rgba(139,92,246,0.5)', borderRadius: 4 },
          { label: 'P99', data: [891, 1100, 1400], backgroundColor: 'rgba(245,158,11,0.5)', borderRadius: 4 },
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: { usePointStyle: true, pointStyle: 'rect', font: { size: 10 }, color: '#6B7280', padding: 8 }
          },
          tooltip: {
            backgroundColor: 'rgba(17,24,39,0.95)',
            titleColor: '#F9FAFB',
            bodyColor: '#D1D5DB',
            padding: 10,
            cornerRadius: 8,
            callbacks: { label: ctx => ' ' + ctx.dataset.label + ': ' + ctx.parsed.y + 'ms' }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            border: { display: false },
            ticks: { font: { size: 11 }, color: '#9CA3AF' }
          },
          y: {
            grid: { color: 'rgba(0,0,0,0.04)' },
            border: { display: false },
            ticks: { font: { size: 11 }, color: '#9CA3AF', callback: v => v + 'ms' }
          }
        }
      }
    });
  }

  // Live timestamp update
  const lastUpdateEl = document.getElementById('lastUpdate');
  function updateTimestamp() {
    const now = new Date();
    lastUpdateEl.textContent = now.toLocaleTimeString('ko-KR') + ' 업데이트됨';
  }
  updateTimestamp();
  setInterval(updateTimestamp, 30000);

  // Alert banner dismiss
  const closeBtn = document.querySelector('.alert-banner-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      this.closest('.alert-banner').style.display = 'none';
    });
  }

})();
