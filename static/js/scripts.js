function getdepartmentsForFacultySubmenu() {
    fetch('/getdepartments/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        const departmentList = document.getElementById('faculty_departments');

        if (data.length === 0) {
            departmentList.innerHTML = '<li class="submenu-item"><a class="nav-link">No Departments Found</a></li>';
        } else {
            data.forEach(department => {
                const submenuLink = document.createElement('a');
                submenuLink.href = `/subadminfaculty.html?dept_code=${department.code}`;
                submenuLink.className = 'nav-link';
                submenuLink.textContent = department.name;
                const submenuListItem = document.createElement('li');
                submenuListItem.className = 'submenu-item';
                submenuListItem.appendChild(submenuLink);
                departmentList.appendChild(submenuListItem);
            });
            setupNav();
        }
    })
    .catch(error => {
        console.error('Error fetching departments for submenu:', error);
    });
}
function getdepartmentsForSubmenu() {
    fetch('/getdepartments/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        const departmentList = document.getElementById('departments_submenu');

        if (data.length === 0) {
            departmentList.innerHTML = '<li class="submenu-item"><a class="nav-link">No Departments Found</a></li>';
        } else {
            data.forEach(department => {
                const submenuLink = document.createElement('a');
                submenuLink.href = `/admindepartmentreports.html?dept_code=${department.code}`;
                submenuLink.className = 'nav-link';
                submenuLink.textContent = department.name;
                const submenuListItem = document.createElement('li');
                submenuListItem.className = 'submenu-item';
                submenuListItem.appendChild(submenuLink);
                departmentList.appendChild(submenuListItem);
            });
            setupNav();
        }
    })
    .catch(error => {
        console.error('Error fetching departments for submenu:', error);
    });
}

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
    getdepartmentsForFacultySubmenu();
    setupNav();
    getdepartmentsForSubmenu();
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
const links = document.querySelectorAll('a');

links.forEach(link => {
    link.addEventListener('click', () => {
        document.getElementById('loading-spinner').style.display = 'flex';
    });
});
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('loading-spinner').style.display = 'none';
});
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
