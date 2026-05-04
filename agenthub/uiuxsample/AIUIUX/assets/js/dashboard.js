/* =============================================
   대시보드 - 차트 및 인터랙션
   ============================================= */

(function() {
  'use strict';

  // =============================================
  // API 사용량 라인 차트
  // =============================================

  const usageCtx = document.getElementById('apiUsageCanvas');
  if (!usageCtx) return;

  const labels = ['2/13', '2/14', '2/15', '2/16', '2/17', '2/18', '2/19'];

  const datasets = [
    {
      label: 'GPT-4o',
      data: [18200, 22100, 19800, 24300, 21500, 25800, 21432],
      borderColor: '#4F46E5',
      backgroundColor: 'rgba(79,70,229,0.08)',
      tension: 0.4,
      fill: false,
      borderWidth: 2.5,
      pointBackgroundColor: '#4F46E5',
      pointRadius: 3,
      pointHoverRadius: 5,
    },
    {
      label: 'Claude Sonnet 4',
      data: [12400, 14200, 13100, 15900, 14500, 16800, 15891],
      borderColor: '#8B5CF6',
      backgroundColor: 'rgba(139,92,246,0.08)',
      tension: 0.4,
      fill: false,
      borderWidth: 2.5,
      pointBackgroundColor: '#8B5CF6',
      pointRadius: 3,
      pointHoverRadius: 5,
    },
    {
      label: 'Gemini Pro',
      data: [6800, 7200, 6500, 8100, 7400, 8900, 8241],
      borderColor: '#10B981',
      backgroundColor: 'rgba(16,185,129,0.08)',
      tension: 0.4,
      fill: false,
      borderWidth: 2.5,
      pointBackgroundColor: '#10B981',
      pointRadius: 3,
      pointHoverRadius: 5,
    },
    {
      label: '기타',
      data: [2100, 2800, 2400, 3100, 2700, 3500, 2727],
      borderColor: '#F59E0B',
      backgroundColor: 'rgba(245,158,11,0.08)',
      tension: 0.4,
      fill: false,
      borderWidth: 2.5,
      pointBackgroundColor: '#F59E0B',
      pointRadius: 3,
      pointHoverRadius: 5,
    }
  ];

  const usageChart = new Chart(usageCtx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 16,
            font: { size: 12 },
            color: '#6B7280',
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17,24,39,0.95)',
          titleColor: '#F9FAFB',
          bodyColor: '#D1D5DB',
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              return ' ' + context.dataset.label + ': ' + context.parsed.y.toLocaleString() + '회';
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            font: { size: 12 },
            color: '#9CA3AF',
          }
        },
        y: {
          grid: {
            color: 'rgba(0,0,0,0.04)',
            drawBorder: false,
          },
          border: { display: false, dash: [4, 4] },
          ticks: {
            font: { size: 11 },
            color: '#9CA3AF',
            callback: function(v) { return (v/1000).toFixed(0) + 'K'; }
          }
        }
      }
    }
  });

  // Period buttons
  ['btnDay','btnWeek','btnMonth'].forEach(function(id) {
    const btn = document.getElementById(id);
    if (btn) {
      btn.addEventListener('click', function() {
        document.querySelectorAll('#btnDay,#btnWeek,#btnMonth').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        // In a real app, fetch new data here
      });
    }
  });

  // =============================================
  // 비용 도넛 차트
  // =============================================

  const costCtx = document.getElementById('costDonutCanvas');
  if (costCtx) {
    new Chart(costCtx, {
      type: 'doughnut',
      data: {
        labels: ['GPT-4o', 'Claude Sonnet 4', 'Gemini Pro', '기타'],
        datasets: [{
          data: [580, 320, 185, 115],
          backgroundColor: ['#4F46E5', '#8B5CF6', '#10B981', '#F59E0B'],
          borderWidth: 0,
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(17,24,39,0.95)',
            titleColor: '#F9FAFB',
            bodyColor: '#D1D5DB',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                return ' ' + context.label + ': ₩' + context.parsed + 'K';
              }
            }
          }
        }
      }
    });
  }

  // =============================================
  // Consumer bar animation on load
  // =============================================
  const bars = document.querySelectorAll('.consumer-bar-fill');
  bars.forEach(function(bar) {
    const targetWidth = bar.style.width;
    bar.style.width = '0%';
    setTimeout(function() {
      bar.style.width = targetWidth;
    }, 300);
  });

})();
