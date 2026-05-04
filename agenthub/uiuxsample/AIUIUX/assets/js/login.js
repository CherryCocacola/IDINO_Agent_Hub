/* =============================================
   로그인 페이지 - login.js
   ============================================= */

(function () {
  'use strict';

  /* ── DOM refs ── */
  const form          = document.getElementById('lgForm');
  const emailEl       = document.getElementById('lgEmail');
  const passwordEl    = document.getElementById('lgPassword');
  const emailErr      = document.getElementById('lgEmailErr');
  const passwordErr   = document.getElementById('lgPasswordErr');
  const submitBtn     = document.getElementById('lgSubmitBtn');
  const submitText    = document.getElementById('lgSubmitText');
  const submitSpinner = document.getElementById('lgSubmitSpinner');
  const alert         = document.getElementById('lgAlert');
  const alertText     = document.getElementById('lgAlertText');

  const pwToggle      = document.getElementById('lgPwToggle');
  const pwIcon        = document.getElementById('lgPwIcon');

  const forgotLink    = document.getElementById('lgForgotLink');
  const forgotModal   = document.getElementById('lgForgotModal');
  const forgotClose   = document.getElementById('lgForgotClose');
  const forgotCancel  = document.getElementById('lgForgotCancel');
  const forgotSubmit  = document.getElementById('lgForgotSubmit');
  const forgotEmail   = document.getElementById('lgForgotEmail');

  const ssoGoogle     = document.getElementById('lgSsoGoogle');
  const ssoMicrosoft  = document.getElementById('lgSsoMicrosoft');

  const toast         = document.getElementById('lgToast');
  const toastText     = document.getElementById('lgToastText');

  /* ── Helpers ── */
  const isValidEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim());

  function showAlert(msg) {
    alertText.textContent = msg;
    alert.style.display = 'flex';
  }
  function hideAlert() {
    alert.style.display = 'none';
  }

  function setFieldError(errEl, msg) {
    errEl.textContent = msg;
  }
  function clearFieldError(errEl) {
    errEl.textContent = '';
  }

  let toastTimer = null;
  function showToast(msg, duration = 3000) {
    toastText.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), duration);
  }

  /* ── PW Toggle ── */
  pwToggle.addEventListener('click', () => {
    const isHidden = passwordEl.type === 'password';
    passwordEl.type = isHidden ? 'text' : 'password';
    pwIcon.className = isHidden ? 'fas fa-eye-slash' : 'fas fa-eye';
    pwToggle.title = isHidden ? '비밀번호 숨기기' : '비밀번호 보기';
  });

  /* ── Real-time field validation ── */
  emailEl.addEventListener('input', () => {
    if (emailEl.value && !isValidEmail(emailEl.value)) {
      emailEl.classList.add('lg-input-error');
      setFieldError(emailErr, '올바른 이메일 형식을 입력하세요.');
    } else {
      emailEl.classList.remove('lg-input-error');
      clearFieldError(emailErr);
    }
    hideAlert();
  });

  passwordEl.addEventListener('input', () => {
    if (passwordEl.value) {
      passwordEl.classList.remove('lg-input-error');
      clearFieldError(passwordErr);
    }
    hideAlert();
  });

  /* ── Form Submit ── */
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    hideAlert();

    const emailVal    = emailEl.value.trim();
    const passwordVal = passwordEl.value;
    let valid = true;

    /* Email */
    if (!emailVal) {
      emailEl.classList.add('lg-input-error');
      setFieldError(emailErr, '이메일을 입력해주세요.');
      valid = false;
    } else if (!isValidEmail(emailVal)) {
      emailEl.classList.add('lg-input-error');
      setFieldError(emailErr, '올바른 이메일 형식을 입력하세요.');
      valid = false;
    } else {
      emailEl.classList.remove('lg-input-error');
      clearFieldError(emailErr);
    }

    /* Password */
    if (!passwordVal) {
      passwordEl.classList.add('lg-input-error');
      setFieldError(passwordErr, '비밀번호를 입력해주세요.');
      valid = false;
    } else {
      passwordEl.classList.remove('lg-input-error');
      clearFieldError(passwordErr);
    }

    if (!valid) return;

    /* ── Simulate login ── */
    submitBtn.disabled = true;
    submitText.textContent = '로그인 중...';
    submitSpinner.style.display = 'block';

    setTimeout(() => {
      /* Demo: any email / password = success */
      const success = true;

      if (success) {
        showToast('로그인 성공! 대시보드로 이동합니다.');
        setTimeout(() => {
          window.location.href = 'index.html';
        }, 1200);
      } else {
        submitBtn.disabled = false;
        submitText.textContent = '로그인';
        submitSpinner.style.display = 'none';
        showAlert('이메일 또는 비밀번호가 올바르지 않습니다.');
        emailEl.classList.add('lg-input-error');
        passwordEl.classList.add('lg-input-error');
      }
    }, 1600);
  });

  /* ── Forgot PW Modal ── */
  function openForgotModal() {
    forgotModal.classList.add('open');
    setTimeout(() => forgotEmail.focus(), 220);
  }
  function closeForgotModal() {
    forgotModal.classList.remove('open');
    forgotEmail.value = '';
  }

  forgotLink.addEventListener('click', (e) => {
    e.preventDefault();
    /* Pre-fill if email is already typed */
    if (emailEl.value.trim() && isValidEmail(emailEl.value.trim())) {
      forgotEmail.value = emailEl.value.trim();
    }
    openForgotModal();
  });
  forgotClose.addEventListener('click', closeForgotModal);
  forgotCancel.addEventListener('click', closeForgotModal);
  forgotModal.addEventListener('click', (e) => {
    if (e.target === forgotModal) closeForgotModal();
  });

  /* Escape key */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && forgotModal.classList.contains('open')) {
      closeForgotModal();
    }
  });

  forgotSubmit.addEventListener('click', () => {
    const val = forgotEmail.value.trim();
    if (!val) {
      forgotEmail.focus();
      forgotEmail.classList.add('lg-input-error');
      return;
    }
    if (!isValidEmail(val)) {
      forgotEmail.classList.add('lg-input-error');
      return;
    }
    forgotEmail.classList.remove('lg-input-error');

    /* Simulate sending */
    forgotSubmit.disabled = true;
    forgotSubmit.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i>전송 중...';

    setTimeout(() => {
      forgotSubmit.disabled = false;
      forgotSubmit.innerHTML = '<i class="fas fa-paper-plane me-2"></i>재설정 링크 전송';
      closeForgotModal();
      showToast(`재설정 링크를 ${val} 로 전송했습니다.`, 4000);
    }, 1500);
  });

  /* ── SSO Buttons ── */
  ssoGoogle.addEventListener('click', () => {
    ssoGoogle.disabled = true;
    ssoGoogle.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i><span>연결 중...</span>';
    setTimeout(() => {
      ssoGoogle.disabled = false;
      ssoGoogle.innerHTML = '<i class="fab fa-google"></i><span>Google로 로그인</span>';
      showToast('Google SSO는 현재 데모 환경에서 지원되지 않습니다.', 3500);
    }, 1200);
  });

  ssoMicrosoft.addEventListener('click', () => {
    ssoMicrosoft.disabled = true;
    ssoMicrosoft.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i><span>연결 중...</span>';
    setTimeout(() => {
      ssoMicrosoft.disabled = false;
      ssoMicrosoft.innerHTML = '<i class="fab fa-microsoft"></i><span>Microsoft로 로그인</span>';
      showToast('Microsoft SSO는 현재 데모 환경에서 지원되지 않습니다.', 3500);
    }, 1200);
  });

  /* ── Auto-focus ── */
  emailEl.focus();

})();
