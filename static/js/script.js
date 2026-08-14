const root = document.documentElement;
const themeButton = document.querySelector('#themeToggle');
const updateThemeIcon = () => { if (themeButton) { themeButton.innerHTML = root.dataset.theme === 'dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>'; } };
updateThemeIcon();
themeButton?.addEventListener('click', () => { root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark'; localStorage.setItem('newshub-theme', root.dataset.theme); updateThemeIcon(); });

const menuButton = document.querySelector('#menuToggle');
const nav = document.querySelector('#mainNav');
menuButton?.addEventListener('click', () => { const open = nav.classList.toggle('open'); menuButton.setAttribute('aria-expanded', String(open)); menuButton.innerHTML = open ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-bars"></i>'; });

document.querySelectorAll('.alert button').forEach(button => button.addEventListener('click', () => button.parentElement.remove()));
document.querySelectorAll('.password-toggle').forEach(button => button.addEventListener('click', () => { const input = button.parentElement.querySelector('input'); input.type = input.type === 'password' ? 'text' : 'password'; button.innerHTML = input.type === 'password' ? '<i class="fa-regular fa-eye"></i>' : '<i class="fa-regular fa-eye-slash"></i>'; }));

const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); } }), { threshold: .08 });
document.querySelectorAll('.reveal').forEach(element => observer.observe(element));

document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => { const button = form.querySelector('button[type="submit"],button:not([type])'); if (button && !button.classList.contains('icon-button')) { button.classList.add('loading'); button.setAttribute('aria-busy', 'true'); } }));

// Scroll progress bar
const progress = document.querySelector('#scrollProgress');
if (progress) {
    const updateProgress = () => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        progress.style.width = height > 0 ? (scrollTop / height) * 100 + '%' : '0%';
    };
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
}

// Newsletter form feedback (front-end only)
const newsletterForm = document.querySelector('.newsletter form');
newsletterForm?.addEventListener('submit', () => {
    const input = newsletterForm.querySelector('input');
    if (input && input.checkValidity()) {
        const button = newsletterForm.querySelector('button');
        const original = button.innerHTML;
        button.innerHTML = '<i class="fa-solid fa-check"></i> Subscribed';
        input.value = '';
        setTimeout(() => { button.innerHTML = original; }, 2500);
    }
});
