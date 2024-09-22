function setupNav() {
    const navLinks = document.querySelectorAll('.nav-link');
    const submenus = document.querySelectorAll('.submenu');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.parentElement.classList.contains('has-submenu')) {
                e.preventDefault(); 
                this.classList.toggle('active');
                const submenu = this.nextElementSibling;
                submenu.style.transition = 'max-height 0.3s ease-in-out'; 
    
                if (submenu.style.maxHeight) {
                    submenu.style.maxHeight = null; 
                } else {
                    submenu.style.maxHeight = submenu.scrollHeight + 'px'; 
                }
                const arrow = this.querySelector('.bi'); 
                arrow.classList.toggle('bi-caret-right-fill');
                arrow.classList.toggle('bi-caret-down-fill'); 
            }
        });
    });
}
document.addEventListener('DOMContentLoaded', function() { 
    setupNav();
    const themeToggle = document.getElementById('themeControlToggle');
    const body = document.body;

    themeToggle.addEventListener('change', () => {
        body.classList.toggle('dark-mode');
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });

    const storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'dark') {
        body.classList.add('dark-mode');
        themeToggle.checked = true; 
    }
});
function showSpinner() {
    document.getElementById('loading-spinner').style.display = 'flex';
}

function hideSpinner() {
    document.getElementById('loading-spinner').style.display = 'none';
}