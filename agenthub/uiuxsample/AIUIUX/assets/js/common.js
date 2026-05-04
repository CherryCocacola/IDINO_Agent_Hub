/* =============================================
   AI 통합관리시스템 - 공통 스크립트
   ============================================= */

(function() {
  'use strict';

  // Sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const mainWrapper = document.getElementById('mainWrapper');
  const topbar = document.querySelector('.topbar');

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
      } else {
        sidebar.classList.toggle('collapsed');
        mainWrapper.classList.toggle('sidebar-collapsed');
        topbar.classList.toggle('sidebar-collapsed');
      }
    });
  }

  // Close sidebar on mobile overlay click
  document.addEventListener('click', function(e) {
    if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open')) {
      if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    }
  });

  // Active nav item from current URL
  const navItems = document.querySelectorAll('.nav-item');
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  navItems.forEach(function(item) {
    const href = item.getAttribute('href');
    if (href === currentPage) {
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
    }
  });

})();
