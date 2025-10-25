const userAvatarBtn = document.getElementById('userAvatarBtn');
const userDropdown = document.getElementById('userDropdown');
const notificationBellBtn = document.getElementById('notificationBellBtn');
const notificationsSidebar = document.getElementById('notificationsSidebar');
const notificationsOverlay = document.getElementById('notificationsOverlay');
const notificationsCloseBtn = document.getElementById('notificationsCloseBtn');
const markAllReadBtn = document.getElementById('markAllReadBtn');
const notificationsContent = document.getElementById('notificationsContent');
const profileBtn = document.getElementById('profileBtn');
const settingsBtn = document.getElementById('settingsBtn');
const logoutBtn = document.getElementById('logoutBtn');

// Toggle user dropdown menu
userAvatarBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle('active');
    userAvatarBtn.classList.toggle('active');
    closeSidebar();
});

// Toggle notifications sidebar
notificationBellBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    openSidebar();
    userDropdown.classList.remove('active');
    userAvatarBtn.classList.remove('active');
});

// Close sidebar when close button is clicked
notificationsCloseBtn.addEventListener('click', closeSidebar);

// Close sidebar when overlay is clicked
notificationsOverlay.addEventListener('click', closeSidebar);

// Close dropdown and sidebar when clicking outside
document.addEventListener('click', (e) => {
    if (!userAvatarBtn.contains(e.target) && !userDropdown.contains(e.target)) {
        userDropdown.classList.remove('active');
        userAvatarBtn.classList.remove('active');
    }
});

// Prevent sidebar from closing when clicking inside it
notificationsSidebar.addEventListener('click', (e) => {
    e.stopPropagation();
});

// Functions
function openSidebar() {
    notificationsSidebar.classList.add('active');
    notificationsOverlay.classList.add('active');
}

function closeSidebar() {
    notificationsSidebar.classList.remove('active');
    notificationsOverlay.classList.remove('active');
}

// Mark all notifications as read
markAllReadBtn.addEventListener('click', () => {
    const unreadItems = notificationsContent.querySelectorAll('.notification-item.unread');
    unreadItems.forEach(item => {
        item.classList.remove('unread');
    });
});

// Sample dropdown actions
profileBtn.addEventListener('click', () => {
    console.log('Profile clicked');
    userDropdown.classList.remove('active');
    userAvatarBtn.classList.remove('active');
});

settingsBtn.addEventListener('click', () => {
    console.log('Settings clicked');
    userDropdown.classList.remove('active');
    userAvatarBtn.classList.remove('active');
});

logoutBtn.addEventListener('click', () => {
    console.log('Logout clicked');
    window.location.href = '/auth/logout';
    // In production, this would handle actual logout
});

// Close sidebar on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeSidebar();
        userDropdown.classList.remove('active');
        userAvatarBtn.classList.remove('active');
    }
});